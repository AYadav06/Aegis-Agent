import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY")
MODEL=os.getenv("MODEL")
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")