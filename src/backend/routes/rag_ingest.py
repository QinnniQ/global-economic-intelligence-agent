# src/backend/routes/rag_ingest.py

from fastapi import APIRouter
from src.backend.rags.rag_store import ingest_pdfs

router = APIRouter()

@router.post("/rag/ingest")
def rag_ingest():
    """
    Ingest all PDFs from the data/reports_pdfs directory.
    """
    return ingest_pdfs()
