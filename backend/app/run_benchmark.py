import json
import os
import time
from typing import Any, Dict, List

from app.agent.PlanExecute import plan_execute_agent
from app.agent.ReAct_agent import run_agent

BENCHMARK_TASKS: List[Dict[str, str]] = [
    {
        "id": "T01",
        "category": "Basic Arithmetic",
        "description": "Single-step division using calculator",
        "task": "What is 1542 divided by 6?",
    },
    {
        "id": "T02",
        "category": "Chained Math",
        "description": "Two-step calculation (multiply then divide)",
        "task": "First multiply 14 by 15, then take that result and divide it by 7.",
    },
    {
        "id": "T03",
        "category": "Code Execution",
        "description": "Algorithmic logic (sum of primes below 30)",
        "task": "Write and execute Python code to find the sum of all prime numbers strictly below 30.",
    },
    {
        "id": "T04",
        "category": "Code Execution",
        "description": "String manipulation via Python code_exec",
        "task": "Use Python code execution to reverse the words in the string 'production grade resilient autonomous agent'.",
    },
    {
        "id": "T05",
        "category": "Live Weather",
        "description": "Single-city temperature lookup via Open-Meteo",
        "task": "What is the current temperature in Berlin in celsius?",
    },
    {
        "id": "T06",
        "category": "Comparative Weather",
        "description": "Multi-entity query comparing Tokyo and Paris",
        "task": "Compare the current temperatures of Tokyo and Paris in celsius. Which city is warmer and by how much?",
    },
    {
        "id": "T07",
        "category": "Weather + Math",
        "description": "Weather retrieval followed by arithmetic scaling",
        "task": "Get the temperature of London in celsius, then calculate what that temperature is multiplied by 1.8.",
    },
    {
        "id": "T08",
        "category": "Web Search",
        "description": "Factual entity search via Tavily API",
        "task": "Search for who won the ICC Men's T20 World Cup in 2024 and which team was the runner up.",
    },
    {
        "id": "T09",
        "category": "Search + Math",
        "description": "Factual retrieval followed by percentage calculation",
        "task": "Search for the current population of Iceland, then use the calculator to compute 5 percent of that population.",
    },
    {
        "id": "T10",
        "category": "Multi-Tool Pipeline",
        "description": "Search data extraction feeding into Python calculation",
        "task": "Search for the speed of light in vacuum in meters per second, then use Python code execution to calculate how many seconds light takes to travel 384,400 kilometers to the Moon.",
    },
]

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BENCHMARK_DIR)
RESULTS_FILE = os.path.join(BACKEND_DIR, "benchmark_results.json")


def save_results(results: List[Dict[str, Any]]):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def run_benchmarks(selected_task: str = None, selected_mode: str = None, reset: bool = False):
    results: List[Dict[str, Any]] = []
    if reset and os.path.exists(RESULTS_FILE):
        try:
            os.remove(RESULTS_FILE)
            print("Cleared previous benchmark_results.json.")
        except Exception:
            pass

    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = []

    tasks = BENCHMARK_TASKS
    if selected_task:
        tasks = [t for t in BENCHMARK_TASKS if t["id"].lower() == selected_task.lower() or selected_task.lower() in t["category"].lower()]
        if not tasks:
            print(f"No task matching '{selected_task}'. Available IDs: {[t['id'] for t in BENCHMARK_TASKS]}")
            return

    print(f"Starting Aegis Architectural Benchmark")
    print(f"Tasks to run: {len(tasks)} | Selected mode: {selected_mode or 'Both (ReAct & Plan→Execute)'}\n")

    for idx, item in enumerate(tasks, 1):
        task_id = item["id"]
        category = item["category"]
        description = item["description"]
        query = item["task"]

        print(f"\n{'='*60}")
        print(f"[{idx}/{len(tasks)}] {task_id}: {category} - {description}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        # --- 1. ReAct Evaluation ---
        if not selected_mode or selected_mode.lower() in ["react", "both"]:
            print("\n▶ Running ReAct...")
            react_entry = next((r for r in results if r["task_id"] == task_id and r["mode"] == "ReAct"), None)
            if not react_entry:
                t0 = time.time()
                try:
                    react_res = run_agent(query, max_iterations=5, return_trace=True)
                    react_elapsed = round(time.time() - t0, 2)
                    react_trace = react_res.get("trace", [])
                    react_usage = react_res.get("usage", {})
                    react_answer = react_res.get("answer", "")
                    success = bool(react_answer and "error" not in react_answer.lower() and "reached maximum" not in react_answer.lower())

                    react_entry = {
                        "task_id": task_id,
                        "category": category,
                        "description": description,
                        "query": query,
                        "mode": "ReAct",
                        "success": success,
                        "llm_calls": react_usage.get("llm_calls", 0),
                        "tool_steps": len(react_trace),
                        "prompt_tokens": react_usage.get("prompt_tokens", 0),
                        "completion_tokens": react_usage.get("completion_tokens", 0),
                        "total_tokens": react_usage.get("total_tokens", 0),
                        "elapsed_seconds": react_elapsed,
                        "answer_preview": react_answer[:140].replace("\n", " "),
                    }
                except Exception as e:
                    react_entry = {
                        "task_id": task_id,
                        "category": category,
                        "description": description,
                        "query": query,
                        "mode": "ReAct",
                        "success": False,
                        "llm_calls": 0,
                        "tool_steps": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "elapsed_seconds": round(time.time() - t0, 2),
                        "error": str(e),
                        "answer_preview": f"Error: {e}",
                    }
                results.append(react_entry)
                save_results(results)
                print(f"✔ ReAct complete: {react_entry['elapsed_seconds']}s | {react_entry['total_tokens']} tokens | {react_entry['llm_calls']} LLM calls")
            else:
                print("↺ ReAct already recorded, skipping.")

        # --- 2. Plan-and-Execute Evaluation ---
        if not selected_mode or selected_mode.lower() in ["plan", "plan_execute", "plan-execute", "both"]:
            print("\n▶ Running Plan→Execute...")
            pe_entry = next((r for r in results if r["task_id"] == task_id and r["mode"] == "Plan→Execute"), None)
            if not pe_entry:
                t0 = time.time()
                try:
                    pe_res = plan_execute_agent(query, allow_replan=False, return_trace=True)
                    pe_elapsed = round(time.time() - t0, 2)
                    pe_trace = pe_res.get("trace", [])
                    pe_usage = pe_res.get("usage", {})
                    pe_answer = pe_res.get("answer", "")
                    success = bool(pe_answer and "error" not in pe_answer.lower())

                    pe_entry = {
                        "task_id": task_id,
                        "category": category,
                        "description": description,
                        "query": query,
                        "mode": "Plan→Execute",
                        "success": success,
                        "llm_calls": pe_usage.get("llm_calls", 0),
                        "tool_steps": len(pe_trace),
                        "prompt_tokens": pe_usage.get("prompt_tokens", 0),
                        "completion_tokens": pe_usage.get("completion_tokens", 0),
                        "total_tokens": pe_usage.get("total_tokens", 0),
                        "elapsed_seconds": pe_elapsed,
                        "answer_preview": pe_answer[:140].replace("\n", " "),
                    }
                except Exception as e:
                    pe_entry = {
                        "task_id": task_id,
                        "category": category,
                        "description": description,
                        "query": query,
                        "mode": "Plan→Execute",
                        "success": False,
                        "llm_calls": 0,
                        "tool_steps": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "elapsed_seconds": round(time.time() - t0, 2),
                        "error": str(e),
                        "answer_preview": f"Error: {e}",
                    }
                results.append(pe_entry)
                save_results(results)
                print(f"✔ Plan→Execute complete: {pe_entry['elapsed_seconds']}s | {pe_entry['total_tokens']} tokens | {pe_entry['llm_calls']} LLM calls")
            else:
                print("↺ Plan→Execute already recorded, skipping.")

    print("\n" + "="*60)
    print("BENCHMARK EXECUTION COMPLETED!")
    print(f"Saved results to {RESULTS_FILE}")
    print("="*60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Aegis ReAct vs Plan-Execute Benchmarks")
    parser.add_argument("--task", type=str, default=None, help="Filter by task ID (e.g. T01, T02)")
    parser.add_argument("--mode", type=str, default=None, choices=["react", "plan_execute", "both"], help="Run only specific agent mode")
    parser.add_argument("--reset", action="store_true", help="Clear previous benchmark_results.json before running")
    args = parser.parse_args()

    run_benchmarks(selected_task=args.task, selected_mode=args.mode, reset=args.reset)
