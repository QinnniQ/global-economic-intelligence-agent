# src/backend/routes/macro_live.py

from fastapi import APIRouter
from src.backend.tools.macro_fetcher import get_indicator

router = APIRouter()

@router.get("/macro/live_chart")
def macro_live_chart(country: str = "US", indicator: str = "NY.GDP.MKTP.KD.ZG"):
    """
    Returns cleaned macro data for charting.
    """
    data = get_indicator(country, indicator)

    if isinstance(data, dict) and "error" in data:
        return data

    # Convert values into chart-friendly format
    cleaned = []
    for row in data:
        if row["value"] is not None:
            cleaned.append(row)

    return {
        "country": country,
        "indicator": indicator,
        "values": cleaned  # [{"date":"2022","value":2.4}, ...]
    }
