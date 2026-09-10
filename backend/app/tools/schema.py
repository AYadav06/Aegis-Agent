TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string","description":"City name , e.g 'London"},
                    "unit":{ "type":"string","enum":["celsius","fahrenheit"],"description":"Temperature unit"}
                },
                "required": ["city"],
            }
        }
    },
    {
        "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform basic arithmetic operations: add, subtract, multiply, divide",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation"
                },
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["operation", "a", "b"]
            }
        }
    },
 {
        "type":"function",
        "function":{
            "name":"search",
            "description":"Search the web for a query",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{"type":"string","description":"search the query"}
                },
                "required":["query"]
            }
        }
    }
]
