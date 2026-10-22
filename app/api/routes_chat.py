"""Chat router."""
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.agent.orchestrator import VoiceOpsAgent
from app.agent.memory import memory_manager

router = APIRouter(tags=["Chat"])
agent = VoiceOpsAgent()


@router.post("/chat", response_model=ChatResponse)
def chat_turn(req: ChatRequest):
    try:
        res = agent.respond(
            message=req.message,
            conversation_id=req.conversation_id,
            step_mode=req.step_mode
        )
        return ChatResponse(
            reply=res["reply"],
            decision=res["decision"],
            source_chunks=res["source_chunks"],
            tool_calls=res["tool_calls"],
            session_id=res["session_id"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
def get_conversation_history(conversation_id: str):
    session = memory_manager.get_or_create(conversation_id)
    return {
        "conversation_id": session.conversation_id,
        "verification_status": session.verification_status,
        "order_id": session.order_id,
        "turns_count": len(session.turns),
        "turns": [t.model_dump() for t in session.turns]
    }
