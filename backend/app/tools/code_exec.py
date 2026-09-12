import os
import subprocess
import sys
import tempfile
from typing import Any, Dict

MAX_OUTPUT_CHARS = 8000


def code_exec(code: str, timeout: int = 10) -> Dict[str, Any]:
    """Execute a Python code snippet in a sandboxed subprocess and return stdout, stderr, and exit code.

    Parameters:
    - code: The Python source code string to execute.
    - timeout: Maximum execution time in seconds (clamped between 1 and 30).
    """
    if not isinstance(code, str) or not code.strip():
        return {
            "success": False,
            "error_type": "INVALID_INPUT",
            "error": "Code parameter must be a non-empty string.",
            "stdout": "",
            "stderr": "",
            "returncode": -1,
        }

    # Clamp timeout to reasonable bounds
    clamped_timeout = max(1, min(int(timeout), 30))

    # Run inside an isolated temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = os.path.join(temp_dir, "script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            completed_proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=clamped_timeout,
                cwd=temp_dir,
            )

            stdout = completed_proc.stdout or ""
            stderr = completed_proc.stderr or ""

            # Truncate output if excessively long to protect LLM context window
            if len(stdout) > MAX_OUTPUT_CHARS:
                stdout = stdout[:MAX_OUTPUT_CHARS] + "\n... [Output truncated]"
            if len(stderr) > MAX_OUTPUT_CHARS:
                stderr = stderr[:MAX_OUTPUT_CHARS] + "\n... [Error output truncated]"

            return {
                "success": completed_proc.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": completed_proc.returncode,
            }

        except subprocess.TimeoutExpired as e:
            stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
            stderr = (e.stderr or "") if isinstance(e.stderr, str) else ""
            return {
                "success": False,
                "error_type": "TIMEOUT",
                "error": f"Execution timed out after {clamped_timeout} seconds.",
                "stdout": stdout,
                "stderr": stderr,
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "error_type": "EXECUTION_ERROR",
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }
