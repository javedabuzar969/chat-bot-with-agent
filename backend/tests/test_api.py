import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_tts_endpoint(client):
    res = client.post("/api/tts", json={"text": "Hello Jarvis"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/mpeg")
    assert len(res.content) > 0


def test_chat_requires_keys(client, monkeypatch):
    # Without real Groq key the agent call will fail, but the endpoint
    # should at least accept the request and stream an error event.
    res = client.post("/api/chat", json={"session_id": "t", "message": "hi"})
    assert res.status_code == 200
    assert "token" in res.text or "error" in res.text
