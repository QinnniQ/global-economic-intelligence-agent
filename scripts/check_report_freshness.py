"""Find new report links on official publisher indexes for human review.

Use --baseline after examining current links; --check in a scheduled workflow.
The script never downloads candidate PDFs or changes the public catalog.
"""

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
WATCH = ROOT / "data" / "report_watch.json"
BASELINE = ROOT / "data" / "report_watch_baseline.json"
CANDIDATE = ROOT / "tmp" / "report_watch_candidate.json"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.words = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.words = []

    def handle_data(self, data):
        if self.href:
            self.words.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            self.links.append((self.href, " ".join(self.words)))
            self.href = None


def discover(item):
    with urlopen(item["url"], timeout=20) as response:
        html = response.read(4_000_000).decode("utf-8", "replace")
    parser = Links()
    parser.feed(html)
    pattern = re.compile(item["link_pattern"], re.I)
    found = set()
    years = "|".join(str(year) for year in range(datetime.now(timezone.utc).year, datetime.now(timezone.utc).year + 3))
    for href, label in parser.links:
        url = urljoin(item["url"], href).split("#", 1)[0]
        if urlparse(url).scheme != "https":
            continue
        if not re.search(rf"(?:{years})", f"{url} {label}"):
            continue
        if pattern.search(f"{url} {label}"):
            found.add(url)
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--baseline", action="store_true", help="Accept reviewed publisher links as baseline")
    group.add_argument("--check", action="store_true", help="Flag links not in the reviewed baseline")
    args = parser.parse_args()
    watched = json.loads(WATCH.read_text(encoding="utf-8"))
    result = {item["id"]: {"index": item["url"], "links": discover(item)} for item in watched}
    if args.baseline:
        BASELINE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Recorded {sum(len(item['links']) for item in result.values())} reviewed links in {BASELINE}")
        return 0
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    new = {key: sorted(set(item["links"]) - set(baseline.get(key, {}).get("links", []))) for key, item in result.items()}
    CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE.write_text(json.dumps({"newLinks": new, "current": result}, indent=2) + "\n", encoding="utf-8")
    for key, links in new.items():
        for link in links:
            print(f"NEW {key}: {link}")
    if any(new.values()):
        print("Review publisher links and the PDF edition before updating the manifest or baseline.")
        return 2
    print(f"No new report links on the {len(watched)} watched publisher indexes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
