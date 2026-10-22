"""Automated tests for Gnani voice integration, text normalization, and audio pipeline."""
import pytest
from pathlib import Path
from app.voice.normalizer import normalize_for_speech
from app.voice.mock_speech import generate_mock_wav
from app.voice.gnani_client import VoiceClient
from app.agent.orchestrator import VoiceOpsAgent


@pytest.fixture
def voice():
    return VoiceClient()


@pytest.fixture
def test_audio_file(tmp_path):
    wav_bytes = generate_mock_wav(duration_sec=0.5)
    audio_path = tmp_path / "test_input.wav"
    audio_path.write_bytes(wav_bytes)
    return audio_path


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


def test_voice_transcribe(voice, test_audio_file):
    res = voice.transcribe(test_audio_file, language_code="en-IN")
    assert "transcript" in res
    assert res["latency_ms"] >= 0
    assert len(res["transcript"]) > 0


def test_voice_synthesize(voice, tmp_path):
    out_file = tmp_path / "test_reply.wav"
    wav_bytes, meta = voice.synthesize("Thank you for contacting ZentroMart.", output_file=out_file)
    assert len(wav_bytes) > 44
    assert out_file.exists()
    assert meta["latency_ms"] >= 0


def test_full_voice_turn(voice, test_audio_file, tmp_path):
    agent = VoiceOpsAgent()
    out_audio = tmp_path / "turn_reply.wav"
    res = voice.voice_turn(
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
