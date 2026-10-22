"""Mock speech generator for testing and offline environments."""
import wave
import io
import math
import struct
from pathlib import Path
from typing import Dict, Any


def generate_mock_wav(duration_sec: float = 1.0, freq: float = 440.0) -> bytes:
    """Generate valid 16kHz PCM 16-bit mono WAV bytes."""
    sample_rate = 16000
    n_samples = int(sample_rate * duration_sec)
    
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)      # mono
        wf.setsampwidth(2)      # 16-bit
        wf.setframerate(sample_rate)
        
        frames = []
        for i in range(n_samples):
            # Generate soft sine wave
            val = int(math.sin(2 * math.pi * freq * (i / sample_rate)) * 10000)
            frames.append(struct.pack("<h", val))
        wf.writeframes(b"".join(frames))
        
    return buf.getvalue()


class MockSpeechEngine:
    """Simulates STT and TTS when live Gnani credentials are not available."""
    
    def transcribe(self, audio_path: str | Path | bytes, language_code: str = "en-IN") -> Dict[str, Any]:
        return {
            "transcript": "Hello, I need help with my order 8978 2837.",
            "language_code": language_code,
            "mocked": True
        }

    def synthesize(self, text: str, voice: str = "Kaveri", model: str = "timbre-v2.5",
                   language: str = "en-IN", output_file: str | Path | None = None) -> bytes:
        wav_bytes = generate_mock_wav(duration_sec=1.5)
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "wb") as f:
                f.write(wav_bytes)
        return wav_bytes
