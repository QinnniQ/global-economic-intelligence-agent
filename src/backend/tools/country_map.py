# src/backend/tools/country_map.py

COUNTRY_MAP = {
    "united states": "US",
    "usa": "US",
    "us": "US",
    "america": "US",

    "germany": "DE",
    "deutschland": "DE",
    "de": "DE",

    "france": "FR",
    "fr": "FR",

    "united kingdom": "GB",
    "uk": "GB",
    "britain": "GB",

    "european union": "EU",
    "eurozone": "EU",
    "eu": "EU",
}

def detect_country(text: str, default="US"):
    text = text.lower()
    for name, code in COUNTRY_MAP.items():
        if name in text:
            return code
    return default
