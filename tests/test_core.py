import os

os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
os.environ.setdefault("MODEL", "gpt-4o-mini")

from fastapi.testclient import TestClient

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
