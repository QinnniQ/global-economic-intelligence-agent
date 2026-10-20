"""Review the dated saved fixture against current World Bank observations.

This script never rewrites the public fixture. It records a candidate under tmp/
and exits nonzero for revised fixture values or a snapshot older than 30 days.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "web" / "src" / "demoSnapshot.json"
CANDIDATE = ROOT / "tmp" / "demo_snapshot_candidate.json"


def retrieve(country: str, indicator: str, year: int) -> tuple[float, str | None, int | None]:
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?" + urlencode({
        "format": "json", "date": f"{year}:{datetime.now(timezone.utc).year}", "per_page": 100,
    })
    last_error = None
    for attempt in range(2):
        try:
            with urlopen(url, timeout=15) as response:
                payload = json.load(response)
            if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[1], list):
                raise ValueError("World Bank returned an invalid response")
            rows = [row for row in payload[1] if isinstance(row, dict) and isinstance(row.get("value"), (int, float))
                    and str(row.get("obs_status", "")).strip().upper() != "F"]
            matching = next((row for row in rows if str(row.get("date")) == str(year)), None)
            if not matching:
                raise ValueError(f"No observed value for {year}")
            latest = max((int(row["date"]) for row in rows if str(row.get("date", "")).isdigit()), default=None)
            updated = payload[0].get("lastupdated") if isinstance(payload[0], dict) else None
            return float(matching["value"]), updated, latest
        except Exception as error:
            last_error = error
            if attempt == 0:
                time.sleep(1)
    raise RuntimeError(f"{country} {indicator}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Check age and fixture structure without network")
    args = parser.parse_args()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(snapshot["reviewedAt"].replace("Z", "+00:00"))).days
    assert len(snapshot["values"]) == 5 and all(len(items) == 3 for items in snapshot["values"].values()), "fixture must cover five countries and three indicators"
    result = {"reviewedAt": snapshot["reviewedAt"], "ageDays": age, "changes": [], "checks": []}
    if not args.offline:
        for country, indicators in snapshot["values"].items():
            for indicator, saved in indicators.items():
                actual, updated, latest = retrieve(country, indicator, saved["year"])
                check = {"country": country, "indicator": indicator, "savedYear": saved["year"],
                         "savedValue": saved["value"], "currentValueForSavedYear": actual,
                         "latestObservedYear": latest, "providerUpdatedAt": updated}
                result["checks"].append(check)
                if abs(actual - saved["value"]) > 0.051:
                    result["changes"].append(check)
    CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved snapshot reviewed {age} days ago; {len(result['changes'])} same-year value changes across {len(result['checks'])} API checks.")
    print(f"Details: {CANDIDATE}")
    if age > 30 or result["changes"]:
        print("Review the candidate; do not silently replace the dated demonstration.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
