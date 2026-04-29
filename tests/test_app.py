import pytest
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers

def test_get_candidates(client):
    response = client.get("/api/candidates")
    assert response.status_code == 200
    data = response.get_json()
    assert "candidates" in data
    assert len(data["candidates"]) == 3

def test_get_candidate_success(client):
    response = client.get("/api/candidate/1")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Aarav Mehta"

def test_get_candidate_not_found(client):
    response = client.get("/api/candidate/999")
    assert response.status_code == 404
    assert "error" in response.get_json()

def test_get_timeline(client):
    response = client.get("/api/timeline")
    assert response.status_code == 200
    assert "events" in response.get_json()
    assert len(response.get_json()["events"]) > 0

def test_get_booths(client):
    response = client.get("/api/booths")
    assert response.status_code == 200
    assert "booths" in response.get_json()

def test_get_turnout(client):
    response = client.get("/api/turnout")
    assert response.status_code == 200
    assert "current" in response.get_json()

def test_get_history(client):
    response = client.get("/api/history")
    assert response.status_code == 200
    assert "history" in response.get_json()

def test_get_quiz(client):
    response = client.get("/api/quiz")
    assert response.status_code == 200
    assert "questions" in response.get_json()
    assert len(response.get_json()["questions"]) == 5

def test_voter_impact(client):
    response = client.get("/api/impact")
    assert response.status_code == 200
    assert "last_margin" in response.get_json()

def test_get_integrity_success(client):
    response = client.get("/api/integrity-score/1")
    assert response.status_code == 200
    assert "breakdown" in response.get_json()

def test_get_integrity_not_found(client):
    response = client.get("/api/integrity-score/999")
    assert response.status_code == 404

def test_compare_candidates(client):
    response = client.post("/api/compare", json={"ids": [1, 2]})
    assert response.status_code == 200
    assert len(response.get_json()["candidates"]) == 2

def test_voter_check_valid(client):
    response = client.post("/api/voter-check", json={"epic": "ABC1234567"})
    assert response.status_code == 200
    assert response.get_json()["registered"] is True

def test_voter_check_invalid(client):
    response = client.post("/api/voter-check", json={"epic": "XY"})
    assert response.status_code == 400
    assert response.get_json()["registered"] is False

def test_voter_check_empty(client):
    response = client.post("/api/voter-check", json={"epic": ""})
    assert response.status_code == 400
    assert response.get_json()["registered"] is False

def test_list_constituencies(client):
    response = client.get("/api/constituencies")
    assert response.status_code == 200
    assert len(response.get_json()["constituencies"]) > 0

def test_list_constituencies_filtered(client):
    response = client.get("/api/constituencies?q=mumbai")
    assert response.status_code == 200
    assert "Mumbai North" in response.get_json()["constituencies"]

def test_security_headers(client):
    response = client.get("/api/candidates")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"

def test_fact_check(client, mock_chat):
    response = client.post("/api/fact-check", json={"claim": "test"})
    assert response.status_code == 200
    assert "verdict" in response.get_json()

def test_chat(client, mock_chat):
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert response.status_code == 200
    assert "reply" in response.get_json()
