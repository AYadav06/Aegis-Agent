from app.config import  OPENROUTER_API_KEY
from openrouter import OpenRouter


client = OpenRouter(
    api_key=OPENROUTER_API_KEY
    )
