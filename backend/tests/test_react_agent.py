import unittest
from unittest.mock import MagicMock, patch

from app.agent.ReAct_agent import run_agent, tracker


class TestReActAgent(unittest.TestCase):
    @patch("app.ReAct_agent.client.chat.send")
    def test_run_agent_direct_answer(self, mock_send):
        mock_msg = MagicMock()
        mock_msg.tool_calls = None
        mock_msg.content = "Paris is the capital of France."
        mock_msg.reasoning = None
        mock_msg.reasoning_details = None

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=mock_msg)]
        mock_resp.usage = MagicMock(prompt_tokens=20, completion_tokens=10)

        mock_send.return_value = mock_resp

        result = run_agent("What is the capital of France?")
        self.assertEqual(result, "Paris is the capital of France.")
        self.assertEqual(tracker.llm_calls, 1)
        self.assertEqual(tracker.prompt_tokens, 20)
        self.assertEqual(tracker.completion_tokens, 10)
        self.assertEqual(tracker.total_tokens, 30)


if __name__ == "__main__":
    unittest.main()
