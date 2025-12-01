# src/backend/routes/rag_search.py

from fastapi import APIRouter
from src.backend.rags.rag_store import search_reports

router = APIRouter()

@router.get("/rag/search")
def rag_search(query: str):
    results = search_reports(query)
    return {
        "query": query,
        "results": results
    }
