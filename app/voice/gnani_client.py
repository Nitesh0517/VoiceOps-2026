"""Gnani.ai Voice Integration (STT & TTS) with Latency Measurement."""
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from app.config import settings
from app.voice.normalizer import normalize_for_speech
from app.voice.mock_speech import MockSpeechEngine

logger = logging.getLogger(__name__)


class VoiceClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GNANI_API_KEY or os.getenv("GNANI_API_KEY", "")
        self.mock_engine = MockSpeechEngine()
        self.is_live = False
        self.stt_client = None
        self.tts_client = None

        if self.api_key and self.api_key.strip():
            try:
                from gnani.stt import GnaniSTTClient
                from gnani.tts import GnaniTTSClient
                self.stt_client = GnaniSTTClient(api_key=self.api_key)
                self.tts_client = GnaniTTSClient(api_key=self.api_key)
                self.is_live = True
                logger.info("Gnani STT/TTS client initialized with live API credentials.")
            except Exception as e:
                logger.warning(f"Could not initialize live Gnani client ({e}). Falling back to mock engine.")
        else:
            logger.info("GNANI_API_KEY not configured. Running voice layer in mock / offline mode.")

    def transcribe(self, audio_path: str | Path, language_code: str = "en-IN") -> Dict[str, Any]:
        """Transcribe audio file using Gnani STT REST."""
        t0 = time.perf_counter()
        if self.is_live and self.stt_client:
            try:
                res = self.stt_client.transcribe(audio_path, language_code=language_code)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                transcript = res.get("transcript", "")
                return {
                    "transcript": transcript,
                    "latency_ms": round(elapsed_ms, 2),
                    "is_live": True,
                    "language_code": language_code
                }
            except Exception as e:
                logger.error(f"Live Gnani STT failed ({e}), falling back to mock.")
                
        # Mock fallback
        res = self.mock_engine.transcribe(audio_path, language_code=language_code)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return {
            "transcript": res["transcript"],
            "latency_ms": round(elapsed_ms, 2),
            "is_live": False,
            "language_code": language_code
        }

    def synthesize(self, text: str, voice: str = "Kaveri", model: str = "timbre-v2.5",
                   language: str = "en-IN", output_file: str | Path | None = None) -> Tuple[bytes, Dict[str, Any]]:
        """Synthesize text to speech using Gnani TTS."""
        t0 = time.perf_counter()
        normalized_text = normalize_for_speech(text)
        
        if self.is_live and self.tts_client:
            try:
                wav_bytes = self.tts_client.synthesize(
                    normalized_text,
                    voice=voice,
                    model=model,
                    language=language,
                    output_file=output_file
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                return wav_bytes, {
                    "latency_ms": round(elapsed_ms, 2),
                    "is_live": True,
                    "normalized_text": normalized_text
                }
            except Exception as e:
                logger.error(f"Live Gnani TTS failed ({e}), falling back to mock.")
                
        # Mock fallback
        wav_bytes = self.mock_engine.synthesize(
            normalized_text,
            voice=voice,
            model=model,
            language=language,
            output_file=output_file
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return wav_bytes, {
            "latency_ms": round(elapsed_ms, 2),
            "is_live": False,
            "normalized_text": normalized_text
        }

    def voice_turn(self, audio_path: str | Path, agent, conversation_id: str = "voice_turn_session",
                   language_code: str = "en-IN", output_file: str | Path = "reply.wav") -> Dict[str, Any]:
        """
        Full Turn: Audio In -> STT -> Agent Brain -> Normalization -> TTS -> Audio Out.
        """
        t_start = time.perf_counter()
        
        # 1. Speech to text
        stt_res = self.transcribe(audio_path, language_code=language_code)
        heard = stt_res["transcript"].strip()
        
        # 2. Agent response
        t_agent_0 = time.perf_counter()
        if not heard:
            reply_text = "Sorry, I didn't catch that. Could you say it again?"
            agent_res = {"reply": reply_text, "source_chunks": [], "tool_calls": []}
        else:
            agent_res = agent.respond(heard, conversation_id=conversation_id, step_mode=3)
            reply_text = agent_res["reply"]
        agent_latency_ms = (time.perf_counter() - t_agent_0) * 1000
        
        # 3. Text to speech
        wav_bytes, tts_info = self.synthesize(
            reply_text,
            voice="Kaveri",
            model="timbre-v2.5",
            language=language_code,
            output_file=output_file
        )
        
        total_latency_ms = (time.perf_counter() - t_start) * 1000
        
        return {
            "heard": heard,
            "reply": reply_text,
            "audio_file": str(output_file),
            "audio_bytes_length": len(wav_bytes),
            "source_chunks": agent_res.get("source_chunks", []),
            "tool_calls": agent_res.get("tool_calls", []),
            "latencies": {
                "stt_ms": stt_res["latency_ms"],
                "agent_ms": round(agent_latency_ms, 2),
                "tts_ms": tts_info["latency_ms"],
                "total_ms": round(total_latency_ms, 2)
            },
            "is_live": self.is_live
        }
