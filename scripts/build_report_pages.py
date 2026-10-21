"""Build private Worker assets with page text from the hash-verified PDF corpus."""

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "public" / "report-pages.v1"


def page_text(page) -> str:
    raw = unicodedata.normalize("NFKC", page.extract_text() or "")
    return re.sub(r"\s+", " ", raw).strip()[:16000]


def build() -> dict[str, bytes]:
    manifest = json.loads((ROOT / "data" / "report_manifest.json").read_text(encoding="utf-8"))
    artifacts = {}
    for report in manifest:
        pdf = ROOT / "data" / "reports_pdfs" / report["file"]
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != report["sha256"]:
            raise ValueError(f"Checksum mismatch: {pdf.name}")
        reader = PdfReader(str(pdf))
        if len(reader.pages) != report["pages"]:
            raise ValueError(f"Page count mismatch: {pdf.name}")
        pages = [page_text(page) for page in reader.pages]
        result = {"version": 1, "id": pdf.stem, "sha256": report["sha256"], "pages": pages}
        artifacts[f"{pdf.stem}.json"] = (json.dumps(result, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    return artifacts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = build()
    if args.check:
        for name, content in artifacts.items():
            if not (OUTPUT / name).is_file() or (OUTPUT / name).read_bytes() != content:
                raise SystemExit(f"Report page artifact is stale: {name}")
        print(f"Verified {len(artifacts)} report page artifacts.")
    else:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for name, content in artifacts.items():
            (OUTPUT / name).write_bytes(content)
        print(f"Wrote {len(artifacts)} report page artifacts ({sum(map(len, artifacts.values())):,} bytes).")
