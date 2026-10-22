"""Chat schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Customer message")
    conversation_id: str = Field(default="default_session", description="Conversation session ID")
    step_mode: int = Field(default=3, ge=1, le=3, description="1: Baseline, 2: RAG, 3: Full Agent")


class ChatResponse(BaseModel):
    reply: str
    decision: str
    source_chunks: List[str]
    tool_calls: List[str]
    session_id: str
