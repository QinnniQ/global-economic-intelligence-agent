# src/backend/routes/report_generate.py

import os
from fastapi import APIRouter
from fastapi.responses import FileResponse
from src.agent.economic_agent import analyze_economy
from src.backend.tools.pdf_generator import generate_economic_report

router = APIRouter()

@router.get("/report/generate")
def generate_report(query: str, country: str = None):
    """
    Generates a PDF report for the given economic query.
    """
    result = analyze_economy(query, country)

    os.makedirs("reports_out", exist_ok=True)
    filepath = f"reports_out/report_{result['country']}.pdf"

    generate_economic_report(
        filepath=filepath,
        country=result["country"],
        indicators=result["indicators_used"],
        analysis=result["analysis"],
        rag_passages=result["rag_passages"],
    )

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=f"Economic_Report_{result['country']}.pdf"
    )
