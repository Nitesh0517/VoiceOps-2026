"""Voice endpoints for STT, TTS, and complete voice turns."""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from app.config import settings
from app.voice.gnani_client import VoiceClient
from app.agent.orchestrator import VoiceOpsAgent
from app.schemas.voice import TranscribeResponse, VoiceRespondResponse

router = APIRouter(prefix="/voice", tags=["Voice"])
voice_client = VoiceClient()
agent = VoiceOpsAgent()

AUDIO_TEMP_DIR = settings.BASE_DIR / "data" / "audio_temp"
AUDIO_TEMP_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language_code: str = Form("en-IN")
):
    temp_path = AUDIO_TEMP_DIR / f"upload_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        res = voice_client.transcribe(temp_path, language_code=language_code)
        return TranscribeResponse(
            transcript=res["transcript"],
            latency_ms=res["latency_ms"],
            is_live=res["is_live"],
            language_code=language_code
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.post("/respond", response_model=VoiceRespondResponse)
async def voice_respond(
    file: UploadFile = File(...),
    conversation_id: str = Form("voice_session"),
    language_code: str = Form("en-IN")
):
    temp_in = AUDIO_TEMP_DIR / f"in_{file.filename}"
    temp_out = AUDIO_TEMP_DIR / f"out_{conversation_id}.wav"
    try:
        with open(temp_in, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        res = voice_client.voice_turn(
            audio_path=temp_in,
            agent=agent,
            conversation_id=conversation_id,
            language_code=language_code,
            output_file=temp_out
        )
        
        return VoiceRespondResponse(
            heard=res["heard"],
            reply=res["reply"],
            audio_url=f"/voice/audio/{temp_out.name}",
            audio_bytes_length=res["audio_bytes_length"],
            source_chunks=res["source_chunks"],
            tool_calls=res["tool_calls"],
            latencies=res["latencies"],
            is_live=res["is_live"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_in.exists():
            temp_in.unlink()


@router.get("/audio/{filename}")
def get_audio_file(filename: str):
    file_path = AUDIO_TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")
