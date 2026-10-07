import os
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
os.environ.setdefault("MODEL", "gpt-4o-mini")

from fastapi.testclient import TestClient

from src.agent import economic_agent
from src.agent.economic_agent import detect_indicators
from src.backend.server import app
from src.backend.tools.country_map import detect_country


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_detect_country_known_country():
    assert detect_country("What is the inflation outlook for Germany?") == "DE"


def test_detect_country_uses_default_when_unknown():
    assert detect_country("What is the inflation outlook?") == "US"


def test_detect_indicators_single_indicator():
    assert set(detect_indicators("What is the inflation outlook?")) == {
        "FP.CPI.TOTL.ZG"
    }


def test_detect_indicators_multiple_indicators():
    assert set(detect_indicators("Compare GDP growth and unemployment")) == {
        "NY.GDP.MKTP.KD.ZG",
        "SL.UEM.TOTL.ZS",
    }


def test_detect_indicators_defaults_to_gdp_and_inflation():
    assert set(detect_indicators("Give me a general economic overview")) == {
        "NY.GDP.MKTP.KD.ZG",
        "FP.CPI.TOTL.ZG",
    }


def test_report_context_keeps_retrieval_ids_and_skips_empty_passages():
    context, passages = economic_agent.format_report_context(
        {"ids": [["weo_chunk_7", "weo_chunk_8"]], "documents": [["  Growth slowed.  ", " "]]}
    )
    assert context == "[weo_chunk_7] Growth slowed."
    assert passages == [{"id": "weo_chunk_7", "text": "Growth slowed."}]


def test_analysis_discloses_missing_report_evidence(monkeypatch):
    prompts = []

    def fake_create(**kwargs):
        prompts.append(kwargs["messages"][0]["content"])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Macro data only; no report evidence."))]
        )

    monkeypatch.setattr(economic_agent, "get_indicator", lambda *_: [{"date": "2025", "value": 2.1}])
    monkeypatch.setattr(economic_agent, "summarize_indicator", lambda *_: "Inflation was 2.1% in the fixture.")
    monkeypatch.setattr(economic_agent, "get_rag_context", lambda *_, **__: ("", []))
    monkeypatch.setattr(
        economic_agent,
        "client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))),
    )

    result = economic_agent.analyze_economy("What is Germany's inflation outlook?")

    assert result["rag_status"] == "no_report_evidence"
    assert result["rag_sources"] == []
    assert "State that report evidence was unavailable" in prompts[-1]
    assert "No report passages were retrieved" in prompts[-1]


def test_analysis_exposes_passage_ids_and_requests_citations(monkeypatch):
    prompts = []

    def fake_create(**kwargs):
        prompts.append(kwargs["messages"][0]["content"])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="The fixture's inflation is 2.1%. The sample report notes easing price pressure [sample_chunk_1]."
            ))]
        )

    monkeypatch.setattr(economic_agent, "get_indicator", lambda *_: [{"date": "2025", "value": 2.1}])
    monkeypatch.setattr(economic_agent, "summarize_indicator", lambda *_: "Inflation was 2.1% in the fixture.")
    monkeypatch.setattr(
        economic_agent,
        "get_rag_context",
        lambda *_, **__: (
            "[sample_chunk_1] Price pressure eased in the sample report.",
            [{"id": "sample_chunk_1", "text": "Price pressure eased in the sample report."}],
        ),
    )
    monkeypatch.setattr(
        economic_agent,
        "client",
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))),
    )

    result = economic_agent.analyze_economy("What is Germany's inflation outlook?")

    assert result["rag_status"] == "passages_found"
    assert result["rag_sources"] == ["sample_chunk_1"]
    assert "[sample_chunk_1] Price pressure eased" in prompts[-1]
    assert "Cite a passage ID" in prompts[-1]
