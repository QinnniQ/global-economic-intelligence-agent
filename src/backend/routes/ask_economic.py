# src/backend/routes/ask_economic.py

from fastapi import APIRouter, HTTPException
from openai import RateLimitError
from src.agent.economic_agent import analyze_economy

router = APIRouter()


@router.get("/ask-economic")
def ask_economic(query: str, country: str = None):
    """
    Main economic question endpoint.
    Attempts to detect country from query if not provided.
    """
    try:
        return analyze_economy(query, country)
    except RateLimitError as exc:
        message = str(exc)
        if "insufficient_quota" in message or "credit_balance_exhausted" in message:
            detail = "OpenAI API credits are exhausted. Add API credits and retry."
        else:
            detail = "OpenAI API rate limit reached. Please retry shortly."
        raise HTTPException(status_code=503, detail=detail) from exc
