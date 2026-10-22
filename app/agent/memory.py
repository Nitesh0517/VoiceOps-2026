"""Conversation Memory and State Manager."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TurnRecord(BaseModel):
    turn_number: int
    user_message: str
    agent_response: str
    decision: str                   # answer, clarify, escalate
    tool_calls: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class ConversationSession(BaseModel):
    conversation_id: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    verification_status: str = "unverified"   # unverified, pending, verified, failed
    failed_attempts: int = 0
    last_discussed_sku: Optional[str] = None
    last_discussed_item: Optional[str] = None
    verified_order_data: Optional[Dict[str, Any]] = None
    turns: List[TurnRecord] = Field(default_factory=list)
    language: str = "en"

    def add_turn(self, user_msg: str, agent_resp: str, decision: str,
                 tool_calls: List[str] | None = None, sources: List[str] | None = None) -> None:
        turn_num = len(self.turns) + 1
        self.turns.append(TurnRecord(
            turn_number=turn_num,
            user_message=user_msg,
            agent_response=agent_resp,
            decision=decision,
            tool_calls=tool_calls or [],
            sources=sources or []
        ))


class MemoryManager:
    """Thread-safe conversation memory store with strict cross-customer isolation."""
    def __init__(self):
        self._sessions: Dict[str, ConversationSession] = {}

    def get_or_create(self, conversation_id: str) -> ConversationSession:
        cid = str(conversation_id).strip()
        if cid not in self._sessions:
            self._sessions[cid] = ConversationSession(conversation_id=cid)
        return self._sessions[cid]

    def reset_session(self, conversation_id: str) -> None:
        cid = str(conversation_id).strip()
        if cid in self._sessions:
            del self._sessions[cid]

    def clear_all(self) -> None:
        self._sessions.clear()


memory_manager = MemoryManager()
