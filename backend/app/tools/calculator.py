def calculator(operation: str, a: float, b: float) -> float:
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: division by zero"
    }
    return {
        "success":True,
        "expression":operation,
        "result":operations[operation]
    } 