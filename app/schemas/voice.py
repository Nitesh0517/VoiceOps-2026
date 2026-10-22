"""Voice schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TranscribeResponse(BaseModel):
    transcript: str
    latency_ms: float
    is_live: bool
    language_code: str


class VoiceRespondResponse(BaseModel):
    heard: str
    reply: str
    audio_url: str
    audio_bytes_length: int
    source_chunks: List[str]
    tool_calls: List[str]
    latencies: Dict[str, float]
    is_live: bool
