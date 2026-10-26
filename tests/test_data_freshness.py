"""The monitor must fail closed when World Bank observations cannot be checked."""

import io
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

import pytest

from scripts import check_data_freshness as freshness


def response(value=1.1, year=2024):
    return io.StringIO(json.dumps([{"lastupdated": "2026-10-01"}, [
        {"date": str(year), "value": value}, {"date": str(year + 1), "value": 2.0},
    ]]))


def test_timeout_is_retried_with_configured_timeout_and_exponential_backoff(monkeypatch):
    attempts = []
    delays = []

    def fake_urlopen(url, timeout):
        attempts.append((url, timeout))
        if len(attempts) < 3:
            raise TimeoutError("read timed out")
        return response()

    monkeypatch.setattr(freshness, "urlopen", fake_urlopen)
    monkeypatch.setattr(freshness.time, "sleep", delays.append)

    assert freshness.retrieve("NL", "NY.GDP.MKTP.KD.ZG", 2024,
                              timeout=4, max_attempts=3, backoff_seconds=0.5) == (1.1, "2026-10-01", 2025)
    assert len(attempts) == 3
    assert all(timeout == 4 for _, timeout in attempts)
    assert delays == [0.5, 1.0]


def test_exhausted_network_retries_fail_without_a_validated_value(monkeypatch):
    calls = []
    delays = []

    def fake_urlopen(url, timeout):
        calls.append(url)
        raise URLError("upstream unavailable")

    monkeypatch.setattr(freshness, "urlopen", fake_urlopen)
    monkeypatch.setattr(freshness.time, "sleep", delays.append)

    with pytest.raises(freshness.UpstreamAPIError, match="NL NY.GDP.MKTP.KD.ZG.*3 attempts.*observation not validated"):
        freshness.retrieve("NL", "NY.GDP.MKTP.KD.ZG", 2024, max_attempts=3)
    assert len(calls) == 3
    assert delays == [1, 2]


def test_retryable_http_error_recovers_but_permanent_error_does_not_retry(monkeypatch):
    calls = []
    delays = []

    def fake_urlopen(url, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise HTTPError(url, 503, "Unavailable", {}, None)
        return response()

    monkeypatch.setattr(freshness, "urlopen", fake_urlopen)
    monkeypatch.setattr(freshness.time, "sleep", delays.append)
    assert freshness.retrieve("NL", "NY.GDP.MKTP.KD.ZG", 2024)[0] == 1.1
    assert len(calls) == 2
    assert delays == [1]

    calls.clear()

    def bad_request(url, timeout):
        calls.append(url)
        raise HTTPError(url, 400, "Bad Request", {}, None)

    monkeypatch.setattr(freshness, "urlopen", bad_request)
    with pytest.raises(freshness.UpstreamAPIError, match="HTTP 400.*not retryable"):
        freshness.retrieve("NL", "NY.GDP.MKTP.KD.ZG", 2024)
    assert len(calls) == 1


def test_missing_observation_is_integrity_failure_without_retry(monkeypatch):
    calls = []
    delays = []

    def fake_urlopen(url, timeout):
        calls.append(url)
        return response(year=2023)

    monkeypatch.setattr(freshness, "urlopen", fake_urlopen)
    monkeypatch.setattr(freshness.time, "sleep", delays.append)
    with pytest.raises(freshness.DataIntegrityError, match="No observed value for 2025"):
        freshness.retrieve("NL", "NY.GDP.MKTP.KD.ZG", 2025)
    assert len(calls) == 1
    assert delays == []


def test_invalid_or_nonfinite_response_is_not_counted_as_a_validation(monkeypatch):
    calls = []
    delays = []

    def fake_urlopen(url, timeout):
        calls.append(url)
        return io.StringIO("not json" if len(calls) == 1 else
                           json.dumps([{"lastupdated": "2026-10-01"}, [{"date": "2024", "value": float("nan")}]]))

    monkeypatch.setattr(freshness, "urlopen", fake_urlopen)
    monkeypatch.setattr(freshness.time, "sleep", delays.append)
    with pytest.raises(freshness.DataIntegrityError, match="invalid World Bank JSON"):
        freshness.retrieve("NL", "NY.GDP.MKTP.KD.ZG", 2024)
    with pytest.raises(freshness.DataIntegrityError, match="No observed value for 2024"):
        freshness.retrieve("NL", "NY.GDP.MKTP.KD.ZG", 2024)
    assert len(calls) == 2
    assert delays == []


@pytest.mark.parametrize("failure, expected_status, expected_category", [
    ("none", 0, None),
    ("upstream", 3, "upstream"),
    ("integrity", 2, "integrity"),
    ("discrepancy", 2, None),
])
def test_monitor_records_failures_and_discrepancies(monkeypatch, tmp_path, failure, expected_status, expected_category):
    fixture = {"reviewedAt": datetime.now(timezone.utc).isoformat(), "values": {
        country: {indicator: {"year": 2024, "value": 1.1} for indicator in ("GDP", "CPI", "UNEMP")}
        for country in ("NL", "DE", "FR", "GB", "US")
    }}
    snapshot = tmp_path / "snapshot.json"
    candidate = tmp_path / "candidate.json"
    snapshot.write_text(json.dumps(fixture), encoding="utf-8")
    monkeypatch.setattr(freshness, "SNAPSHOT", snapshot)
    monkeypatch.setattr(freshness, "CANDIDATE", candidate)

    def fake_retrieve(country, indicator, year, **options):
        if country == "NL" and indicator == "GDP":
            if failure == "upstream":
                raise freshness.UpstreamAPIError("NL GDP: timeout after retries")
            if failure == "integrity":
                raise freshness.DataIntegrityError("NL GDP: no observed value")
            if failure == "discrepancy":
                return 1.2, None, 2025
        return 1.1, None, 2025

    monkeypatch.setattr(freshness, "retrieve", fake_retrieve)
    assert freshness.main(["--request-timeout", "4", "--max-attempts", "2"]) == expected_status
    result = json.loads(candidate.read_text(encoding="utf-8"))
    if expected_category:
        assert len(result["checks"]) == 14
        assert result["changes"] == []
        assert len(result["errors"]) == 1
        assert result["errors"][0]["country"] == "NL"
        assert result["errors"][0]["indicator"] == "GDP"
        assert result["errors"][0]["category"] == expected_category
        assert result["errors"][0]["message"]
    else:
        assert len(result["checks"]) == 15
        assert result["errors"] == []
        assert len(result["changes"]) == (1 if failure == "discrepancy" else 0)
        if failure == "discrepancy":
            assert result["changes"][0]["currentValueForSavedYear"] == 1.2
