"""
ElectIQ Test Suite — 25+ tests covering all endpoints,
security headers, input validation, and Google service integration.
"""
import json
import pytest


# ── Endpoint Tests ────────────────────────────────────────────────────────────

def test_index_returns_200(client):
    assert client.get("/").status_code == 200


def test_candidates_returns_list(client):
    r = client.get("/api/candidates")
    d = json.loads(r.data)
    assert "candidates" in d
    assert len(d["candidates"]) == 3


def test_candidate_by_id(client):
    r = client.get("/api/candidate/1")
    d = json.loads(r.data)
    assert d["name"] == "Aarav Mehta"


def test_candidate_not_found(client):
    assert client.get("/api/candidate/999").status_code == 404


def test_timeline_has_events(client):
    r = client.get("/api/timeline")
    d = json.loads(r.data)
    assert len(d["events"]) > 0


def test_booths_returns_list(client):
    r = client.get("/api/booths")
    assert "booths" in json.loads(r.data)


def test_quiz_has_5_questions(client):
    r = client.get("/api/quiz")
    d = json.loads(r.data)
    assert len(d["questions"]) == 5


def test_impact_returns_data(client):
    d = json.loads(client.get("/api/impact").data)
    assert "last_margin" in d


def test_compare_returns_selected(client):
    r = client.post("/api/compare", json={"ids": [1, 2]}, content_type="application/json")
    d = json.loads(r.data)
    assert len(d["candidates"]) == 2


def test_history_returns_data(client):
    d = json.loads(client.get("/api/history").data)
    assert "history" in d


def test_integrity_score_valid(client):
    d = json.loads(client.get("/api/integrity-score/1").data)
    assert "breakdown" in d


def test_integrity_score_not_found(client):
    assert client.get("/api/integrity-score/999").status_code == 404


def test_constituencies_returns_list(client):
    d = json.loads(client.get("/api/constituencies").data)
    assert len(d["constituencies"]) > 0


def test_constituencies_filtered(client):
    d = json.loads(client.get("/api/constituencies?q=mumbai").data)
    assert any("Mumbai" in c for c in d["constituencies"])


# ── Voter Check Tests ─────────────────────────────────────────────────────────

def test_voter_check_valid_epic(client):
    r = client.post("/api/voter-check", json={"epic": "ABC1234567"}, content_type="application/json")
    assert json.loads(r.data)["registered"] is True


def test_voter_check_invalid_epic_short(client):
    r = client.post("/api/voter-check", json={"epic": "XY"}, content_type="application/json")
    assert json.loads(r.data)["registered"] is False


def test_voter_check_empty_epic(client):
    r = client.post("/api/voter-check", json={"epic": ""}, content_type="application/json")
    assert json.loads(r.data)["registered"] is False


def test_voter_check_xss_attempt(client):
    r = client.post("/api/voter-check", json={"epic": "<script>alert(1)</script>"}, content_type="application/json")
    assert json.loads(r.data)["registered"] is False


def test_voter_check_sql_injection(client):
    r = client.post("/api/voter-check", json={"epic": "'; DROP TABLE--"}, content_type="application/json")
    assert json.loads(r.data)["registered"] is False


# ── Security Header Tests ─────────────────────────────────────────────────────

def test_security_headers_present(client):
    r = client.get("/api/candidates")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in r.headers


def test_404_returns_json(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert "error" in json.loads(r.data)


# ── Google Service Tests ──────────────────────────────────────────────────────

def test_sentiment_endpoint(client, mock_gcp):
    r = client.post("/api/sentiment", json={"text": "Free education for all"}, content_type="application/json")
    d = json.loads(r.data)
    assert "score" in d
    assert "label" in d


def test_sentiment_empty_text(client):
    r = client.post("/api/sentiment", json={"text": ""}, content_type="application/json")
    assert r.status_code == 400


def test_translate_endpoint(client, mock_gcp):
    r = client.post("/api/translate", json={"text": "Vote today", "target": "hi"}, content_type="application/json")
    d = json.loads(r.data)
    assert "translated" in d


def test_translate_invalid_language(client):
    r = client.post("/api/translate", json={"text": "Hello", "target": "zz"}, content_type="application/json")
    assert r.status_code == 400


def test_fact_check_empty(client):
    r = client.post("/api/fact-check", json={"claim": ""}, content_type="application/json")
    assert r.status_code == 400


def test_chat_endpoint(client, mock_chat, mock_gcp):
    r = client.post("/api/chat",
        json={"messages": [{"role": "user", "content": "Who are the candidates?"}], "profile": {}},
        content_type="application/json")
    d = json.loads(r.data)
    assert len(d["reply"]) > 0


def test_turnout_analytics(client):
    """Test BigQuery analytics endpoint returns expected shape."""
    r = client.get("/api/turnout/analytics")
    assert r.status_code == 200
    d = json.loads(r.data)
    assert "rows" in d
    assert "provider" in d


def test_turnout_update_valid(client):
    """Test turnout update with valid value."""
    r = client.post("/api/turnout/update",
        json={"current": 45.5},
        content_type="application/json")
    assert r.status_code == 200
    d = json.loads(r.data)
    assert d.get("success") == True


def test_turnout_update_invalid(client):
    """Test turnout update rejects out-of-range values."""
    r = client.post("/api/turnout/update",
        json={"current": 150},
        content_type="application/json")
    assert r.status_code == 400


def test_entities_endpoint(client, mock_gcp):
    """Test Google NL entity extraction endpoint."""
    r = client.post("/api/entities",
        json={"text": "Prime Minister Modi visited Mumbai North constituency"},
        content_type="application/json")
    assert r.status_code == 200


def test_verify_photo_valid(client):
    """Test Cloud Vision photo verification for valid candidate."""
    r = client.get("/api/verify-photo/1")
    d = json.loads(r.data)
    assert "verified" in d


def test_verify_photo_invalid(client):
    """Test Cloud Vision photo verification for non-existent candidate."""
    assert client.get("/api/verify-photo/999").status_code == 404
