"""Local PDF retrieval corpus for the Python prototype."""

import hashlib
import json
import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_store")
REPORT_MANIFEST = Path("data/report_manifest.json")

# The original index uses Chroma's default local ONNX MiniLM model. Keep both
# ingestion and query embedding functions explicit so they cannot drift apart.
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name="economic_reports",
    embedding_function=DefaultEmbeddingFunction(),
    metadata={"hnsw:space": "cosine"},
)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract the text of a PDF, retaining the original helper's API."""
    return "".join((page.extract_text() or "") + "\n" for page in PdfReader(pdf_path).pages)


def chunk_text(text: str) -> list[str]:
    """Use the same splitter settings as the original corpus."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "],
    )
    return splitter.split_text(text)


def ingest_pdfs(folder_path="data/reports_pdfs", manifest_path=REPORT_MANIFEST):
    """Add manifest-listed PDFs, preserving legacy chunks and existing IDs.

    New chunks are split within each PDF page and carry source, page and file
    fingerprint metadata. A repeat run skips already present IDs, so a partial
    run can be resumed without inserting duplicates.
    """
    reports = {report["file"]: report for report in json.loads(Path(manifest_path).read_text(encoding="utf-8"))}
    chunks_ingested = 0
    reports_ingested = []
    reports_skipped = []

    for pdf_path in sorted(Path(folder_path).glob("*.pdf")):
        report = reports.get(pdf_path.name)
        if report is None:
            raise ValueError(f"PDF is missing from report manifest: {pdf_path.name}")
        base_id = pdf_path.stem
        first_id = collection.get(ids=[f"{base_id}_chunk_0"], include=[])["ids"]
        if report.get("legacy") and first_id:
            reports_skipped.append(base_id)
            continue

        file_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        if file_hash != report["sha256"]:
            raise ValueError(f"PDF checksum changed: {pdf_path.name}")
        reader = PdfReader(pdf_path)
        if len(reader.pages) != report["pages"]:
            raise ValueError(f"PDF page count changed: {pdf_path.name}")

        documents = []
        ids = []
        metadatas = []
        for page_number, page in enumerate(reader.pages, start=1):
            for chunk in chunk_text(page.extract_text() or ""):
                ids.append(f"{base_id}_chunk_{len(ids)}")
                documents.append(chunk)
                metadatas.append({
                    "source_file": pdf_path.name,
                    "source_url": report["url"],
                    "publisher": report["publisher"],
                    "title": report["title"],
                    "issue": report["issue"],
                    "sha256": file_hash,
                    "page": page_number,
                    "index_version": 2,
                })

        if not documents:
            raise ValueError(f"PDF has no extractable text: {pdf_path.name}")
        added = 0
        for start in range(0, len(ids), 128):
            batch_ids = ids[start:start + 128]
            existing = set(collection.get(ids=batch_ids, include=[])["ids"])
            missing = [i for i, chunk_id in enumerate(batch_ids) if chunk_id not in existing]
            if missing:
                collection.add(
                    ids=[batch_ids[i] for i in missing],
                    documents=[documents[start + i] for i in missing],
                    metadatas=[metadatas[start + i] for i in missing],
                )
                added += len(missing)
        chunks_ingested += added
        (reports_ingested if added else reports_skipped).append(base_id)
        print(f"{pdf_path.name}: {added} new chunks, {len(ids)} total", flush=True)

    return {
        "status": "ok",
        "chunks_ingested": chunks_ingested,
        "reports_ingested": reports_ingested,
        "reports_skipped": reports_skipped,
    }


def search_reports(query: str, n=3):
    """Query the local report store using the same local embedding function."""
    return collection.query(query_texts=[query], n_results=n)
