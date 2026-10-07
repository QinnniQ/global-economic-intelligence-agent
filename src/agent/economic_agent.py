# src/agent/economic_agent.py

from openai import OpenAI
from src.backend.config import OPENAI_API_KEY, MODEL
from src.backend.tools.macro_fetcher import get_indicator
from src.backend.tools.country_map import detect_country
from src.backend.rags.rag_store import search_reports

client = OpenAI(api_key=OPENAI_API_KEY)

# Keyword → indicator mapping
INDICATOR_MAP = {
    "gdp": "NY.GDP.MKTP.KD.ZG",
    "growth": "NY.GDP.MKTP.KD.ZG",

    "inflation": "FP.CPI.TOTL.ZG",
    "cpi": "FP.CPI.TOTL.ZG",

    "unemployment": "SL.UEM.TOTL.ZS",
    "jobless": "SL.UEM.TOTL.ZS",
}


def detect_indicators(query: str):
    """
    Scan text for indicator keywords.
    """
    query = query.lower()
    indicators = set()

    for keyword, code in INDICATOR_MAP.items():
        if keyword in query:
            indicators.add(code)

    # Default: if nothing found, return GDP + inflation
    if not indicators:
        return [
            "NY.GDP.MKTP.KD.ZG",     # GDP growth
            "FP.CPI.TOTL.ZG"         # Inflation
        ]

    return list(indicators)


def summarize_indicator(country: str, indicator: str, data: list):
    """
    Given recent macro data, produce a short 2–3 sentence summary.
    """
    rows = [f"{row['date']}: {row['value']}" for row in data[:5]]
    formatted_data = "\n".join(rows)

    prompt = f"""
You are an economic analyst.

Given the following data for country {country} and indicator {indicator},
write a short 2–3 sentence summary describing the trend, direction,
and any notable movements.

Data:
{formatted_data}

Summary:
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def format_report_context(results: dict):
    """Keep Chroma passage IDs alongside text so an answer can be checked."""
    documents = (results.get("documents") or [[]])[0]
    ids = (results.get("ids") or [[]])[0]
    passages = []
    for index, document in enumerate(documents):
        text = (document or "").strip()
        if not text:
            continue
        passage_id = ids[index] if index < len(ids) and ids[index] else f"passage_{index + 1}"
        passages.append({"id": passage_id, "text": text})
    context = "\n\n".join(f"[{p['id']}] {p['text']}" for p in passages)
    return context, passages


def get_rag_context(query: str, n=3):
    """Retrieve report passages with IDs that can be cited in the response."""
    return format_report_context(search_reports(query, n=n))


def analyze_economy(query: str, country: str = None):
    """
    Main economic reasoning pipeline:
    - Detect country
    - Detect relevant indicators
    - Fetch macro data
    - Summarize each indicator with the LLM
    - Retrieve RAG evidence from reports
    - Produce a final combined economic analysis
    """

    # ---- COUNTRY DETECTION ----
    detected_country = detect_country(query, default=country or "US")
    country = detected_country.upper()

    # ---- INDICATOR DETECTION ----
    indicator_list = detect_indicators(query)

    # ---- MACRO DATA + SUMMARIES ----
    collected_data = []
    summaries = []

    for indicator in indicator_list:
        data = get_indicator(country, indicator)

        if isinstance(data, dict) and "error" in data:
            summaries.append(f"Error fetching {indicator}: {data['error']}")
            continue

        # Summarize with LLM
        summary = summarize_indicator(country, indicator, data)
        summaries.append(f"Indicator {indicator}:\n{summary}")

        collected_data.append({
            "indicator": indicator,
            "values": data[:5]
        })

    # ---- RAG CONTEXT ----
    rag_context, rag_passages = get_rag_context(query, n=3)

    # ---- FINAL SYNTHESIS ----
    report_instruction = (
        "Use report excerpts only for claims they actually support. Cite a passage ID in square brackets "
        "for each report-based claim; do not invent citations."
        if rag_passages
        else "No report passages were retrieved. State that report evidence was unavailable; "
        "base the answer only on the macro data and do not invent report claims."
    )
    final_prompt = f"""
User question:
"{query}"

Country detected: {country}
Indicators analyzed: {indicator_list}

=== MACRO TREND SUMMARIES ===
{chr(10).join(summaries)}

=== EXCERPTS FROM ECONOMIC REPORTS (RAG) ===
{rag_context or 'No report passages were retrieved.'}

Write a concise economic analysis (5–8 sentences).

Your answer should:
- integrate the macro trends,
- follow this evidence rule: {report_instruction}
- explain risks, drivers, and outlook,
- avoid repeating raw data verbatim,
- separate evidence from inference.
"""

    final_response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": final_prompt}],
    )

    combined_answer = final_response.choices[0].message.content

    return {
        "country": country,
        "indicators_used": indicator_list,
        "analysis": combined_answer,
        "rag_passages": rag_context,
        "rag_sources": [p["id"] for p in rag_passages],
        "rag_status": "passages_found" if rag_passages else "no_report_evidence",
        "raw_summaries": summaries,
        "raw_data": collected_data
    }
