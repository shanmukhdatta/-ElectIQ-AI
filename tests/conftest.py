"""Shared pytest fixtures for ElectIQ test suite."""
import pytest
from unittest.mock import patch


@pytest.fixture
def client():
    """Create a Flask test client with testing mode enabled."""
    from backend.app import app
    app.config["TESTING"] = True
    app.config["RATELIMIT_ENABLED"] = False
    with app.test_client() as c:
        yield c


@pytest.fixture
def mock_chat():
    """Mock invoke_chat so tests don't need real API keys."""
    with patch("backend.app.invoke_chat", return_value=("Test AI response", "mock")):
        yield


@pytest.fixture
def mock_gcp():
    """Mock all Google Cloud service calls."""
    with patch("backend.google_services.analyse_text_sentiment",
               return_value={"score": 0.5, "magnitude": 0.5, "label": "Positive", "provider": "mock"}), \
         patch("backend.google_services.translate_text",
               return_value={"translated": "अनुवाद", "source_language": "en", "target_language": "hi", "provider": "mock"}), \
         patch("backend.google_services.log_event_to_bigquery", return_value=True), \
         patch("backend.google_services.get_live_turnout", return_value={"current": 34, "last_election": 67}):
        yield
