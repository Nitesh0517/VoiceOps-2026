"""Automated tests for Gnani voice integration, text normalization, and audio pipeline.

Distinguishes offline/mocked tests from live Gnani.ai API integration tests.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from app.voice.normalizer import normalize_for_speech
from app.voice.mock_speech import generate_mock_wav
from app.voice.gnani_client import VoiceClient
from app.agent.orchestrator import VoiceOpsAgent


@pytest.fixture
def mock_voice(monkeypatch):
    """Explicit offline/mock VoiceClient with empty credentials."""
    monkeypatch.delenv("GNANI_API_KEY", raising=False)
    vc = VoiceClient()
    vc.api_key = ""
    vc.is_live = False
    return vc


@pytest.fixture
def test_audio_file(tmp_path):
    wav_bytes = generate_mock_wav(duration_sec=0.5)
    audio_path = tmp_path / "test_input.wav"
    audio_path.write_bytes(wav_bytes)
    return audio_path


# ==========================================
# 1. TEXT NORMALIZATION & AUDIO GENERATION
# ==========================================

def test_text_normalization():
    raw_text = "Your order 89782837 has a reverse pickup fee of ₹49."
    norm = normalize_for_speech(raw_text)
    assert "8 9 7 8, 2 8 3 7" in norm
    assert "49 rupees" in norm
    assert "₹" not in norm


def test_mock_wav_generation():
    wav_bytes = generate_mock_wav(duration_sec=1.0)
    assert len(wav_bytes) > 44  # Valid WAV header is at least 44 bytes
    assert wav_bytes[:4] == b"RIFF"
    assert wav_bytes[8:12] == b"WAVE"


# ==========================================
# 2. OFFLINE / MOCK SPEECH ENGINE TESTS
# ==========================================

def test_voice_transcribe_mock(mock_voice, test_audio_file):
    res = mock_voice.transcribe(test_audio_file, language_code="en-IN")
    assert "transcript" in res
    assert res["latency_ms"] >= 0
    assert len(res["transcript"]) > 0
    assert res["is_live"] is False


def test_voice_synthesize_mock(mock_voice, tmp_path):
    out_file = tmp_path / "test_reply.wav"
    wav_bytes, meta = mock_voice.synthesize("Thank you for contacting ZentroMart.", output_file=out_file)
    assert len(wav_bytes) > 44
    assert out_file.exists()
    assert meta["latency_ms"] >= 0
    assert meta["is_live"] is False


def test_full_voice_turn_mock(mock_voice, test_audio_file, tmp_path):
    agent = VoiceOpsAgent()
    out_audio = tmp_path / "turn_reply.wav"
    res = mock_voice.voice_turn(
        audio_path=test_audio_file,
        agent=agent,
        conversation_id="voice_turn_test",
        language_code="en-IN",
        output_file=out_audio
    )
    assert "heard" in res
    assert "reply" in res
    assert out_audio.exists()
    assert res["audio_bytes_length"] > 0
    assert "latencies" in res
    assert "total_ms" in res["latencies"]
    assert res["is_live"] is False


# ==========================================
# 3. LIVE SDK INTERFACE DISPATCH TESTS (MOCKED)
# ==========================================

def test_voice_live_sdk_dispatch(test_audio_file, tmp_path):
    """Verify that when an API key is provided, VoiceClient routes through Gnani SDK."""
    mock_stt_instance = MagicMock()
    mock_stt_instance.transcribe.return_value = {"transcript": "Where is my order 8978 2837?", "success": True}

    mock_tts_instance = MagicMock()
    dummy_wav = generate_mock_wav(duration_sec=0.5)
    mock_tts_instance.synthesize.return_value = dummy_wav

    with patch("gnani.stt.GnaniSTTClient", return_value=mock_stt_instance), \
         patch("gnani.tts.GnaniTTSClient", return_value=mock_tts_instance):
        
        live_vc = VoiceClient(api_key="gnani_live_test_key_xyz")
        assert live_vc.is_live is True

        # Test STT dispatch
        stt_res = live_vc.transcribe(test_audio_file, language_code="en-IN")
        assert stt_res["is_live"] is True
        assert stt_res["transcript"] == "Where is my order 8978 2837?"
        assert mock_stt_instance.transcribe.called

        # Test TTS dispatch with required model & voice
        out_wav = tmp_path / "live_reply.wav"
        tts_bytes, tts_meta = live_vc.synthesize("Hello Customer", voice="Kaveri", model="timbre-v2.5", output_file=out_wav)
        assert tts_meta["is_live"] is True
        assert len(tts_bytes) > 0
        mock_tts_instance.synthesize.assert_called_with(
            "Hello Customer",
            voice="Kaveri",
            model="timbre-v2.5",
            language="en-IN",
            output_file=out_wav
        )


def test_voice_live_sdk_error_fallback(test_audio_file):
    """Verify that if live SDK call fails, it falls back to mock with error logged."""
    mock_stt_instance = MagicMock()
    mock_stt_instance.transcribe.side_effect = RuntimeError("Gnani STT connection timeout")

    with patch("gnani.stt.GnaniSTTClient", return_value=mock_stt_instance), \
         patch("gnani.tts.GnaniTTSClient"):
        
        live_vc = VoiceClient(api_key="gnani_live_test_key_xyz")
        res = live_vc.transcribe(test_audio_file, language_code="en-IN")
        
        assert res["is_live"] is False
        assert res.get("fallback") is True
        assert "timeout" in res.get("error", "").lower()
        assert len(res["transcript"]) > 0  # Fallback provided valid transcript


# ==========================================
# 4. REAL NETWORK INTEGRATION TEST (CONDITIONAL)
# ==========================================

@pytest.mark.skipif(not os.getenv("GNANI_API_KEY"), reason="GNANI_API_KEY not configured in environment")
def test_real_gnani_network_integration(test_audio_file, tmp_path):
    """
    Live end-to-end network test against official Gnani.ai endpoints.
    Only executed when GNANI_API_KEY is present in the environment.
    """
    vc = VoiceClient()
    assert vc.is_live is True, "VoiceClient should be initialized in live mode when GNANI_API_KEY is set."

    # Live transcribe
    stt_res = vc.transcribe(test_audio_file, language_code="en-IN")
    assert "transcript" in stt_res
    assert stt_res["is_live"] is True

    # Live synthesize
    out_wav = tmp_path / "real_network_reply.wav"
    wav_bytes, meta = vc.synthesize(
        "Welcome to ZentroMart support.",
        voice="Kaveri",
        model="timbre-v2.5",
        language="en-IN",
        output_file=out_wav
    )
    assert len(wav_bytes) > 100
    assert meta["is_live"] is True
    assert out_wav.exists()
