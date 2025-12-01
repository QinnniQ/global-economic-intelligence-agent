# src/backend/routes/ask_basic.py

from fastapi import APIRouter
from src.backend.config import OPENAI_API_KEY, MODEL
from openai import OpenAI

router = APIRouter()

client = OpenAI(api_key=OPENAI_API_KEY)

@router.get("/ask-basic")
def ask_basic(query: str):
    """
    Simple LLM test endpoint.
    Sends the user's query to the model and returns the response.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": query}],
    )

    answer = response.choices[0].message.content

    return {
        "query": query,
        "response": answer
    }
