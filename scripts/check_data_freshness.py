"""Review the dated saved fixture against current World Bank observations.

This script never rewrites the public fixture. It records a candidate under tmp/
and exits nonzero for revised values, a snapshot older than 30 days, or checks
that could not be completed.
"""

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "web" / "src" / "demoSnapshot.json"
CANDIDATE = ROOT / "tmp" / "demo_snapshot_candidate.json"
RETRYABLE_HTTP_STATUSES = {408, 429}


class UpstreamAPIError(RuntimeError):
    """The World Bank request failed, so the observation was not validated."""


class DataIntegrityError(ValueError):
    """The World Bank response could not validate the saved observation."""


def _observations(payload: object, year: int) -> tuple[float, str | None, int | None]:
    if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[0], dict) or not isinstance(payload[1], list):
        raise DataIntegrityError("World Bank returned an invalid response")
    rows = [row for row in payload[1] if isinstance(row, dict) and isinstance(row.get("value"), (int, float))
            and not isinstance(row["value"], bool)
            and math.isfinite(row["value"])
            and str(row.get("obs_status", "")).strip().upper() != "F"]
    matching = next((row for row in rows if str(row.get("date")) == str(year)), None)
    if matching is None:
        raise DataIntegrityError(f"No observed value for {year}")
    latest = max((int(row["date"]) for row in rows if str(row.get("date", "")).isdigit()), default=None)
    return float(matching["value"]), payload[0].get("lastupdated"), latest


def retrieve(country: str, indicator: str, year: int, *, timeout: float = 10,
             max_attempts: int = 3, backoff_seconds: float = 1) -> tuple[float, str | None, int | None]:
    """Fetch an observation, retrying only transient transport and HTTP failures."""
    if timeout <= 0 or max_attempts < 1 or backoff_seconds < 0:
        raise ValueError("timeout and max_attempts must be positive; backoff_seconds must be nonnegative")
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?" + urlencode({
        "format": "json", "date": f"{year}:{datetime.now(timezone.utc).year}", "per_page": 100,
    })
    for attempt in range(1, max_attempts + 1):
        try:
            with urlopen(url, timeout=timeout) as response:
                try:
                    payload = json.load(response)
                except ValueError as error:
                    raise DataIntegrityError(f"{country} {indicator}: invalid World Bank JSON: {error}") from error
            try:
                return _observations(payload, year)
            except DataIntegrityError as error:
                raise DataIntegrityError(f"{country} {indicator}: {error}") from error
        except HTTPError as error:
            if error.code not in RETRYABLE_HTTP_STATUSES and not 500 <= error.code < 600:
                raise UpstreamAPIError(f"{country} {indicator}: World Bank HTTP {error.code} (not retryable)") from error
            reason = f"HTTP {error.code}"
        except (URLError, TimeoutError, ConnectionError) as error:
            reason = str(error)
        if attempt == max_attempts:
            raise UpstreamAPIError(
                f"{country} {indicator}: transient World Bank request failed after "
                f"{max_attempts} attempts ({reason}); observation not validated"
            )
        delay = backoff_seconds * 2 ** (attempt - 1)
        print(f"{country} {indicator}: World Bank request attempt {attempt}/{max_attempts} failed "
              f"({reason}); retrying in {delay:g}s.")
        time.sleep(delay)
    raise AssertionError("unreachable")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Check age and fixture structure without network")
    parser.add_argument("--request-timeout", type=float, default=10, help="Seconds allowed for each World Bank request (default: 10)")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum requests per observation (default: 3)")
    parser.add_argument("--backoff-seconds", type=float, default=1, help="Initial exponential retry delay in seconds (default: 1)")
    args = parser.parse_args(argv)
    if args.request_timeout <= 0 or args.max_attempts < 1 or args.backoff_seconds < 0:
        parser.error("--request-timeout and --max-attempts must be positive; --backoff-seconds must be nonnegative")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(snapshot["reviewedAt"].replace("Z", "+00:00"))).days
    assert len(snapshot["values"]) == 5 and all(len(items) == 3 for items in snapshot["values"].values()), "fixture must cover five countries and three indicators"
    result = {"reviewedAt": snapshot["reviewedAt"], "ageDays": age, "changes": [], "checks": [], "errors": []}
    if not args.offline:
        for country, indicators in snapshot["values"].items():
            for indicator, saved in indicators.items():
                try:
                    actual, updated, latest = retrieve(
                        country, indicator, saved["year"], timeout=args.request_timeout,
                        max_attempts=args.max_attempts, backoff_seconds=args.backoff_seconds,
                    )
                except (UpstreamAPIError, DataIntegrityError) as error:
                    category = "upstream" if isinstance(error, UpstreamAPIError) else "integrity"
                    result["errors"].append({"country": country, "indicator": indicator,
                                             "savedYear": saved["year"], "category": category,
                                             "message": str(error)})
                    print(f"{category.capitalize()} failure: {error}")
                    continue
                check = {"country": country, "indicator": indicator, "savedYear": saved["year"],
                         "savedValue": saved["value"], "currentValueForSavedYear": actual,
                         "latestObservedYear": latest, "providerUpdatedAt": updated}
                result["checks"].append(check)
                if abs(actual - saved["value"]) > 0.051:
                    result["changes"].append(check)
    CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved snapshot reviewed {age} days ago; {len(result['changes'])} same-year value changes "
          f"across {len(result['checks'])} API checks; {len(result['errors'])} incomplete checks.")
    print(f"Details: {CANDIDATE}")
    if age > 30 or result["changes"] or any(error["category"] == "integrity" for error in result["errors"]):
        print("Review the candidate; do not silently replace the dated demonstration.")
        return 2
    if result["errors"]:
        print("World Bank requests could not complete; rerun the monitor before validating the fixture.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
