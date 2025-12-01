# src/backend/tools/macro_fetcher.py

import requests
import pandas as pd

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json"

def get_indicator(country: str, indicator: str):
    """
    Fetches a macroeconomic indicator from the World Bank API.
    
    Example:
        country="US", indicator="NY.GDP.MKTP.KD.ZG" (GDP growth)
    """
    url = WORLD_BANK_BASE_URL.format(country=country, indicator=indicator)

    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"Failed to fetch data: HTTP {response.status_code}"}

    data = response.json()

    # World Bank returns a two-element list: metadata, actual data list
    if not isinstance(data, list) or len(data) < 2:
        return {"error": "Invalid API response structure."}

    records = data[1]  # list of values (one per year)

    # Clean into a simple dataframe
    df = pd.DataFrame(records)

    # Keep only year/value
    df = df[["date", "value"]]

    # Convert to numeric where possible
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Sort by year desc (latest first)
    df = df.sort_values("date", ascending=False)

    # Return top rows as list for JSON compatibility
    return df.to_dict(orient="records")
