# src/backend/routes/rag_ingest.py

import os
import secrets
from fastapi import APIRouter, Header, HTTPException
from src.backend.rags.rag_store import ingest_pdfs

router = APIRouter()

@router.post("/rag/ingest")
def rag_ingest(x_ingest_token: str | None = Header(default=None)):
    """
    Ingest all PDFs from the data/reports_pdfs directory.
    """
    expected = os.getenv("INGEST_ADMIN_TOKEN")
    if not expected or not x_ingest_token or not secrets.compare_digest(x_ingest_token, expected):
        raise HTTPException(status_code=403, detail="Ingestion is disabled or unauthorized.")
    return ingest_pdfs()
