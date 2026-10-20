"""Build a read-only page search index from the 13 verified local PDFs.

The public artifact contains term frequencies and page references, not report
text. Search results take readers to the publisher's PDF page for verification.
"""

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "public" / "report-search-index.v1.json"
STOPWORDS = set("a an and are as at be been by can could do for from had has have how i in into is it its of on or our should than that the their there these this to was were what when where which who will with would you your also report reports page figure table source data".split())


def terms(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return [term for term in re.findall(r"[a-z][a-z0-9]{1,23}", normalized) if term not in STOPWORDS]


def build() -> bytes:
    manifest = json.loads((ROOT / "data" / "report_manifest.json").read_text(encoding="utf-8"))
    reports = []
    pages = []
    postings = defaultdict(list)
    for report in manifest:
        pdf = ROOT / "data" / "reports_pdfs" / report["file"]
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == report["sha256"], pdf.name
        reader = PdfReader(str(pdf))
        assert len(reader.pages) == report["pages"], pdf.name
        report_id = Path(report["file"]).stem
        report_number = len(reports)
        reports.append({key: report[key] for key in ("title", "publisher", "issue", "url", "sha256") } | {"id": report_id})
        for page_number, page in enumerate(reader.pages, start=1):
            frequencies = Counter(terms(page.extract_text() or ""))
            if not frequencies:
                continue
            page_id = len(pages)
            pages.append([report_number, page_number, sum(frequencies.values())])
            for term, frequency in frequencies.items():
                postings[term].append([page_id, min(frequency, 255)])
    artifact = {"version": 1, "stopwords": sorted(STOPWORDS), "reports": reports, "pages": pages,
                "postings": {term: postings[term] for term in sorted(postings)}}
    return (json.dumps(artifact, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = build()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != generated:
            raise SystemExit("Report search index is stale; run python scripts/build_report_search.py")
        print(f"Search index matches all PDFs ({len(generated):,} bytes).")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(generated)
        print(f"Wrote {OUTPUT} ({len(generated):,} bytes).")
