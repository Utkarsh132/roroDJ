from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_role_aware_chat_and_profile() -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "session_id": "test-session",
            "role": "producer",
            "message": "Help me make a 124 BPM house beat and mix it.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "producer"
    assert "house" in data["profile"]["genres"]
    assert data["profile"]["preferences"]["bpm"] == "124"
    assert data["provider"] == "fallback"


def test_invalid_audio_rejected() -> None:
    response = client.post(
        "/api/v1/audio/analyze",
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )
    assert response.status_code == 400

