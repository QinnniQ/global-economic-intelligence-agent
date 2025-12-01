# src/backend/routes/ask_economic.py

from fastapi import APIRouter
from src.agent.economic_agent import analyze_economy

router = APIRouter()

@router.get("/ask-economic")
def ask_economic(query: str, country: str = None):
    """
    Main economic question endpoint.
    Attempts to detect country from query if not provided.
    """
    result = analyze_economy(query, country)
    return result

