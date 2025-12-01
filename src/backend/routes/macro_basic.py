# src/backend/routes/macro_basic.py

from fastapi import APIRouter
from src.backend.tools.macro_fetcher import get_indicator

router = APIRouter()

@router.get("/macro/basic")
def macro_basic(country: str, indicator: str):
    """
    Basic macroeconomic data fetcher.
    Example:
        /macro/basic?country=US&indicator=NY.GDP.MKTP.KD.ZG
    """
    data = get_indicator(country, indicator)
    return {
        "country": country.upper(),
        "indicator": indicator,
        "data": data,
    }
