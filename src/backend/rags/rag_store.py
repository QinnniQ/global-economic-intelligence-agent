# src/backend/rags/rag_store.py

import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader

CHROMA_DIR = "chroma_store"

# Initialize vector DB and embeddings
embeddings = OpenAIEmbeddings()
client = chromadb.PersistentClient(path=CHROMA_DIR)

collection = client.get_or_create_collection(
    name="economic_reports",
    metadata={"hnsw:space": "cosine"}
)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF using pypdf.
    """
    reader = PdfReader(pdf_path)
    full_text = ""

    for page in reader.pages:
        content = page.extract_text()
        if content:
            full_text += content + "\n"

    return full_text


def chunk_text(text: str) -> list:
    """
    Split long text into smaller chunks for embedding.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "]
    )

    chunks = splitter.split_text(text)
    return chunks


def ingest_pdfs(folder_path="data/reports_pdfs"):
    """
    Ingest all PDF files into the Chroma vector store.
    Each chunk becomes a separate document with unique ID.
    """

    all_chunks = []
    all_ids = []

    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf"):

            pdf_path = os.path.join(folder_path, file)
            base_id = os.path.splitext(file)[0]

            print(f"Extracting PDF: {file}")

            text = extract_text_from_pdf(pdf_path)
            chunks = chunk_text(text)

            # Add chunks with unique IDs
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"{base_id}_chunk_{i}")

    if all_chunks:
        print(f"Ingesting {len(all_chunks)} chunks...")
        collection.add(documents=all_chunks, ids=all_ids)
        return {"status": "ok", "chunks_ingested": len(all_chunks)}
    else:
        return {"status": "no_pdfs_found"}


def search_reports(query: str, n=3):
    """
    Query the economic reports vector store.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n
    )

    return results
