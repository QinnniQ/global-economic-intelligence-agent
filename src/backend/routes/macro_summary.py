# src/backend/routes/macro_summary.py

from fastapi import APIRouter
from src.backend.tools.macro_fetcher import get_indicator
from src.backend.config import OPENAI_API_KEY, MODEL
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key=OPENAI_API_KEY)

@router.get("/macro/summary")
def macro_summary(country: str, indicator: str):
    """
    Fetches macroeconomic data, sends it to the LLM, and returns a human-readable summary.
    """

    data = get_indicator(country, indicator)

    # If error from fetcher
    if isinstance(data, dict) and "error" in data:
        return data

    # Prepare compact table-like summary to give LLM structure
    rows = [f"{row['date']}: {row['value']}" for row in data[:6]]  # limit to latest 6 rows
    formatted_data = "\n".join(rows)

    prompt = f"""
You are an economic analyst.

Given this macroeconomic data for country {country.upper()} and indicator '{indicator}', 
write a short, clear summary (3–5 sentences) describing the recent trend, 
whether values are rising or falling, and any notable patterns.

Data:
{formatted_data}

Summary:
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    summary = response.choices[0].message.content

    return {
        "country": country.upper(),
        "indicator": indicator,
        "summary": summary,
        "raw_data": data[:6]
    }
