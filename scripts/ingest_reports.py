"""Ingest manifest-listed PDFs into a local or staged Chroma store.

Example: python scripts/ingest_reports.py --store tmp/chroma-2026-staging
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default="chroma_store", help="Target Chroma directory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))
    os.environ["CHROMA_DIR"] = str(Path(args.store).resolve())
    os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

    from src.backend.rags.rag_store import ingest_pdfs

    print(ingest_pdfs(), flush=True)


if __name__ == "__main__":
    main()
