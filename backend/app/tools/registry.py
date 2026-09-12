from app.tools.calculator import calculator
from app.tools.code_exec import code_exec
from app.tools.search import search
from app.tools.weather import get_weather

TOOL_REGISTRY = {
    "get_weather": get_weather,
    "calculator": calculator,
    "search": search,
    "code_exec": code_exec,
}
