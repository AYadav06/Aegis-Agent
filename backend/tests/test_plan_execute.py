import json
import unittest
from unittest.mock import MagicMock, patch

from app.usage_tracker import UsageTracker
from app.agent.PlanExecute import (
    execute_step,
    llm_call,
    plan,
    plan_execute_agent,
    replan_needed,
)


class TestUsageTracker(unittest.TestCase):
    def test_tracker_reset_and_record(self):
        tracker = UsageTracker()
        tracker.start()
        self.assertEqual(tracker.prompt_tokens, 0)
        self.assertEqual(tracker.completion_tokens, 0)
        self.assertEqual(tracker.llm_calls, 0)

        mock_resp = MagicMock()
        mock_resp.usage.prompt_tokens = 15
        mock_resp.usage.completion_tokens = 25
        tracker.record(mock_resp)

        self.assertEqual(tracker.prompt_tokens, 15)
        self.assertEqual(tracker.completion_tokens, 25)
        self.assertEqual(tracker.total_tokens, 40)
        self.assertEqual(tracker.llm_calls, 1)

        # Ensure start() resets counts
        tracker.start()
        self.assertEqual(tracker.prompt_tokens, 0)
        self.assertEqual(tracker.completion_tokens, 0)
        self.assertEqual(tracker.llm_calls, 0)


class TestExecuteStep(unittest.TestCase):
    def test_execute_calculator_tool(self):
        step = '1. TOOL: calculator | ARGS: {"operation": "multiply", "a": 6, "b": 7}'
        results = {}
        res = execute_step(step, results)
        data = json.loads(res)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("result"), 42)

    def test_execute_unknown_tool(self):
        step = '1. TOOL: non_existent_tool | ARGS: {"x": 1}'
        results = {}
        res = execute_step(step, results)
        self.assertIn("Error: Tool 'non_existent_tool' is not in TOOL_REGISTRY", res)

    def test_placeholder_substitution(self):
        results = {"step_1_result": "10"}
        step = 'TOOL: calculator | ARGS: {"operation": "add", "a": {step_1_result}, "b": 5}'
        res = execute_step(step, results)
        data = json.loads(res)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("result"), 15)

    @patch("app.agent.PlanExecute.client.chat.send")
    def test_think_step(self, mock_send):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="Temperature is moderate."))]
        mock_resp.usage = None
        mock_send.return_value = mock_resp

        step = "2. THINK: Compare the temperature with threshold."
        results = {"step_1_result": '{"temperature": 18}'}
        res = execute_step(step, results)
        self.assertEqual(res, "Temperature is moderate.")


class TestPlanAndReplan(unittest.TestCase):
    @patch("app.agent.PlanExecute.client.chat.send")
    def test_plan_parsing(self, mock_send):
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(
                message=MagicMock(
                    content=(
                        "Here is the plan:\n"
                        '1. TOOL: get_weather | ARGS: {"city": "London"}\n'
                        "2. THINK: check if temperature > 15\n"
                        '3. TOOL: calculator | ARGS: {"operation": "multiply", "a": 20, "b": 1.8}\n'
                    )
                )
            )
        ]
        mock_resp.usage = None
        mock_send.return_value = mock_resp

        steps = plan("Check London weather")
        self.assertEqual(len(steps), 3)
        self.assertTrue(steps[0].startswith("1. TOOL: get_weather"))
        self.assertTrue(steps[1].startswith("2. THINK:"))

    @patch("app.agent.PlanExecute.client.chat.send")
    def test_replan_needed_yes_and_no(self, mock_send):
        mock_resp = MagicMock()
        mock_resp.usage = None

        # When task is complete (LLM answers YES)
        mock_resp.choices = [MagicMock(message=MagicMock(content="YES"))]
        mock_send.return_value = mock_resp
        self.assertFalse(replan_needed("Task", {}))

        # When task is NOT complete (LLM answers NO)
        mock_resp.choices = [MagicMock(message=MagicMock(content="NO"))]
        mock_send.return_value = mock_resp
        self.assertTrue(replan_needed("Task", {}))


class TestEndToEndAgent(unittest.TestCase):
    @patch("app.agent.PlanExecute.client.chat.send")
    def test_plan_execute_flow(self, mock_send):
        # 1. plan response
        plan_resp = MagicMock()
        plan_resp.choices = [
            MagicMock(
                message=MagicMock(
                    content=(
                        '1. TOOL: calculator | ARGS: {"operation": "add", "a": 100, "b": 50}\n'
                        "2. THINK: summarize result\n"
                    )
                )
            )
        ]
        plan_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=10)

        # 2. think response
        think_resp = MagicMock()
        think_resp.choices = [MagicMock(message=MagicMock(content="Total is 150."))]
        think_resp.usage = MagicMock(prompt_tokens=5, completion_tokens=5)

        # 3. replan check response (YES -> complete)
        replan_resp = MagicMock()
        replan_resp.choices = [MagicMock(message=MagicMock(content="YES"))]
        replan_resp.usage = MagicMock(prompt_tokens=5, completion_tokens=2)

        # 4. final answer response
        final_resp = MagicMock()
        final_resp.choices = [MagicMock(message=MagicMock(content="The final result is 150."))]
        final_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=10)

        mock_send.side_effect = [plan_resp, think_resp, replan_resp, final_resp]

        answer = plan_execute_agent("Calculate 100 + 50 and summarize", allow_replan=True)
        self.assertEqual(answer, "The final result is 150.")


if __name__ == "__main__":
    unittest.main()
