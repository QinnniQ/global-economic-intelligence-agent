"""Re-embed stored Chroma documents with Chroma's default local model.

Run against a copy of chroma_store with the repository's pinned requirements.
For example: python scripts/verify_chroma_vectors.py --store tmp/chroma-verification-store --id ecb_chunk_0
Use --all to check every stored vector. This makes no OpenAI API call.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import chromadb
import numpy as np
from chromadb.config import Settings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True, help="Path to a copy of chroma_store")
    parser.add_argument("--id", default="ecb_chunk_0", help="Stored chunk ID for an individual check")
    parser.add_argument("--all", action="store_true", help="Check every stored vector")
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()
    if not (args.store / "chroma.sqlite3").is_file():
        parser.error("--store must contain chroma.sqlite3")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
    client = chromadb.PersistentClient(path=str(args.store.resolve()), settings=Settings(anonymized_telemetry=False))
    collection = client.get_collection("economic_reports")
    model = DefaultEmbeddingFunction()
    print(f"Chroma {chromadb.__version__}; collection {collection.name}; {collection.count()} vectors")

    checked = 0
    worst_difference = 0.0
    worst_cosine = 1.0
    mismatches: list[str] = []
    for offset in range(0, collection.count() if args.all else 1, args.batch_size):
        rows = (
            collection.get(limit=args.batch_size, offset=offset, include=["documents", "embeddings"])
            if args.all
            else collection.get(ids=[args.id], include=["documents", "embeddings"])
        )
        if not rows["ids"]:
            raise SystemExit(f"No stored vector found for {args.id}")
        stored = np.asarray(rows["embeddings"], dtype=np.float32)
        fresh = np.asarray(model(rows["documents"]), dtype=np.float32)
        differences = np.max(np.abs(stored - fresh), axis=1)
        cosine = np.sum(stored * fresh, axis=1) / (
            np.linalg.norm(stored, axis=1) * np.linalg.norm(fresh, axis=1)
        )
        checked += len(rows["ids"])
        worst_difference = max(worst_difference, float(np.max(differences)))
        worst_cosine = min(worst_cosine, float(np.min(cosine)))
        mismatches.extend(rows["ids"][i] for i, difference in enumerate(differences) if difference > 1e-5)
        if not args.all:
            print(f"ID {rows['ids'][0]}; dimensions {stored.shape[1]}")
            print(f"Stored first 8:    {stored[0, :8].tolist()}")
            print(f"Recomputed first 8: {fresh[0, :8].tolist()}")
    print(f"Checked {checked}; minimum cosine {worst_cosine:.8f}; maximum absolute coordinate difference {worst_difference:.9f}")
    print(f"Vectors differing by more than 1e-5: {len(mismatches)}")
    if mismatches:
        print(f"First mismatches: {mismatches[:10]}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
