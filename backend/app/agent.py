import json
from app.client import client
from app.config import MODEL
from app.tools.schema import TOOL_SCHEMAS
from app.tools.registry import TOOL_REGISTRY

SYSTEM_PROMPT = (
    "You are Aegis, an autonomous AI agent that solves tasks using reasoning and tools. "
    "For each step, briefly reason about what you need to do, then call the appropriate tool. "
    "Once you have enough information from tool observations, synthesize a complete and direct final answer."
)


def get_thought(msg, fallback_tool_name: str = None) -> str:
    """Extract model's internal reasoning/thought if present, or provide a fallback."""
    reasoning = getattr(msg, "reasoning", None)
    if reasoning and str(reasoning).strip():
        return str(reasoning).strip()

    details = getattr(msg, "reasoning_details", None)
    if details and isinstance(details, list):
        texts = [getattr(d, "text", "") for d in details if getattr(d, "text", "")]
        if texts:
            return " ".join(texts).strip()

    if msg.content and msg.content.strip():
        return msg.content.strip()

    if fallback_tool_name:
        return f"Need to call tool '{fallback_tool_name}' to gather information for the user query."

    return ""


def format_action(tool_name: str, args) -> str:
    """Format tool call as a clean function signature."""
    if isinstance(args, dict):
        args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
        return f"{tool_name}({args_str})"
    return f"{tool_name}({args})"


def execute_tool_call(tool_name: str, arguments_str: str) -> dict:
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found."}

    try:
        args = (
            json.loads(arguments_str)
            if isinstance(arguments_str, str)
            else arguments_str
        )
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON arguments: {str(e)}"}

    try:
        func = TOOL_REGISTRY[tool_name]
        result = func(**args)
        return result
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}


def run_agent(user_prompt: str, max_iterations: int = 5):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for iteration in range(max_iterations):
        print(f"\n{'='*55}\n🔄 Iteration {iteration + 1}\n{'='*55}")

        # 1. Send conversation history and tool definitions to LLM
        response = client.chat.send(model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        msg = response.choices[0].message

        # 2. If the model did not make any tool calls, return final response
        if not msg.tool_calls:
            thought = get_thought(msg)
            if thought and thought != msg.content:
                print(f"\n🧠 [Thought / Reason]:\n{thought}")
            print(f"\n🏁 [Final Answer]:\n{msg.content}")
            return msg.content

        # 3. Append the assistant's message (which contains the tool calls) to history
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": msg.tool_calls,
            }
        )

        # 4. Iterate over each requested tool call and execute it
        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            tool_id = tool_call.id

            # Parse arguments for display
            try:
                parsed_args = (
                    json.loads(tool_args)
                    if isinstance(tool_args, str)
                    else tool_args
                )
            except Exception:
                parsed_args = tool_args

            # Step 1: Thought / Reason
            thought = get_thought(msg, fallback_tool_name=tool_name)
            if thought:
                print(f"\n🧠 [Thought / Reason]:\n{thought}")

            # Step 2: Action
            print(f"\n⚡ [Action]:\n{format_action(tool_name, parsed_args)}")

            # Execute tool
            tool_result = execute_tool_call(tool_name, tool_args)

            # Step 3: Observation
            if isinstance(tool_result, dict):
                obs_str = json.dumps(tool_result, indent=2)
            else:
                obs_str = str(tool_result)
            print(f"\n🔍 [Observation]:\n{obs_str}")

            # 5. Append the tool output to history with role='tool' and matching tool_call_id
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": json.dumps(tool_result),
                }
            )

    print("\n Reached max iterations without a final answer.")
    return "Agent reached maximum iteration limit."


if __name__ == "__main__":
    import sys

    # Use argument passed from command line, or fallback to default prompt
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What is 1542 divided by 6?"

    print(f"User Query: {query}")
    answer = run_agent(query)
    print(f"\n{'='*55}\nDone! Result: {answer}")
