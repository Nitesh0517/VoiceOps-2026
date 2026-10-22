"""Automated tests for FastAPI endpoints."""
import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.voice.mock_speech import generate_mock_wav

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data


def test_chat_endpoint_turn1():
    resp = client.post("/chat", json={
        "message": "Hello, mujhe apne order ke baare mein help chahiye.",
        "conversation_id": "api_test_conv1",
        "step_mode": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "clarify"
    assert any(k in data["reply"].lower() for k in ["ai", "assistant", "एआई"])


def test_order_lookup_api_identity_gate():
    # 1. Unverified lookup
    resp = client.get("/orders/89782837")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification_required"] is True
    assert data["verified"] is False
    assert data["items"] is None

    # 2. Verified lookup with phone suffix 4533
    resp_v = client.get("/orders/89782837?verification_value=4533")
    assert resp_v.status_code == 200
    data_v = resp_v.json()
    assert data_v["verified"] is True
    assert data_v["found"] is True
    assert data_v["items"] is not None
    assert len(data_v["items"]) >= 1


def test_ticket_creation_api():
    resp = client.post("/tickets", json={
        "summary": "Customer damaged item inquiry requiring manual priority team review.",
        "order_id": "89782837",
        "reason": "damage_claim",
        "intent": "damage"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] is True
    assert data["ticket_id"].startswith("TKT")


def test_voice_transcribe_and_respond_api():
    wav_bytes = generate_mock_wav(duration_sec=0.5)
    file_payload = ("test.wav", io.BytesIO(wav_bytes), "audio/wav")
    
    # 1. Transcribe
    resp_stt = client.post(
        "/voice/transcribe",
        files={"file": file_payload},
        data={"language_code": "en-IN"}
    )
    assert resp_stt.status_code == 200
    assert "transcript" in resp_stt.json()

    # 2. Complete Voice Turn
    file_payload2 = ("test2.wav", io.BytesIO(wav_bytes), "audio/wav")
    resp_voice = client.post(
        "/voice/respond",
        files={"file": file_payload2},
        data={"conversation_id": "api_voice_turn_1", "language_code": "en-IN"}
    )
    assert resp_voice.status_code == 200
    data_v = resp_voice.json()
    assert "heard" in data_v
    assert "reply" in data_v
    assert "audio_url" in data_v
    assert "latencies" in data_v
