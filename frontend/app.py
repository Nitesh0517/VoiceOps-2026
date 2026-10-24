"""Streamlit UI for VoiceOps 2026 AI Customer Support Voice Agent."""
import os
import sys
import time
import tempfile
from pathlib import Path

# Fix Streamlit module shadowing where frontend/app.py shadows top-level 'app' package
_FRONTEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _FRONTEND_DIR.parent
if str(_FRONTEND_DIR) in sys.path:
    sys.path.remove(str(_FRONTEND_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

import streamlit as st
import pandas as pd
from app.config import settings
from app.agent.orchestrator import VoiceOpsAgent
from app.voice.gnani_client import VoiceClient
from app.voice.mock_speech import generate_mock_wav
from app.tools.order_tool import OrderTool
from app.tools.ticket_tool import TicketTool

st.set_page_config(
    page_title="VoiceOps 2026 — ZentroMart AI Voice Agent",
    page_icon="🎙️",
    layout="wide"
)

# Initialize Session State
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = f"session_{int(time.time())}"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = VoiceOpsAgent()
if "voice_client" not in st.session_state:
    st.session_state.voice_client = VoiceClient()
if "order_tool" not in st.session_state:
    st.session_state.order_tool = OrderTool()
if "ticket_tool" not in st.session_state:
    st.session_state.ticket_tool = TicketTool()

# Sidebar: Controls, Configuration & Inspector
with st.sidebar:
    st.title("🎙️ VoiceOps 2026")
    st.caption("ZentroMart AI Customer Support Voice Agent")
    st.divider()

    st.subheader("⚙️ Agent Configuration")
    step_mode = st.radio(
        "Evaluation Step",
        options=[3, 2, 1],
        format_func=lambda x: {
            3: "Step 3: Full Agent (Memory + Tools + RAG)",
            2: "Step 2: RAG Grounded Q&A (No Tools/Memory)",
            1: "Step 1: Baseline Prompt-Only (Guesswork)"
        }[x]
    )

    lang_code = st.selectbox(
        "Language",
        options=["en-IN", "hi-IN"],
        format_func=lambda x: "English (India)" if x == "en-IN" else "Hindi (हिन्दी)"
    )

    st.divider()
    st.subheader("🔑 API Status")
    active_key = os.getenv("GNANI_API_KEY", "") or settings.GNANI_API_KEY
    if active_key and not st.session_state.voice_client.is_live:
        st.session_state.voice_client = VoiceClient()

    if st.session_state.voice_client.is_live:
        st.success("🟢 **Gnani.ai Speech:** Live API")
        st.caption("Model: `timbre-v2.5` | Voice: `Kaveri`")
        if st.button("🔌 Test API Connection", use_container_width=True):
            with st.spinner("Pinging Gnani.ai API..."):
                test_res = st.session_state.voice_client.test_connection()
                if test_res["status"] == "success":
                    st.success(test_res["message"])
                else:
                    st.error(test_res["message"])
    else:
        st.warning("🟠 **Gnani.ai Speech:** Mock Engine (No Key)")
        with st.expander("ℹ️ How to enable Live Voice"):
            st.markdown(
                "1. Get API key from [app.gnani.ai/voice](https://app.gnani.ai/voice)\n"
                "2. Add to `.env` in project root:\n"
                "   ```env\n"
                "   GNANI_API_KEY=your_key_here\n"
                "   ```\n"
                "3. Click button below to reload:"
            )
            if st.button("🔄 Reload Credentials", use_container_width=True):
                from dotenv import load_dotenv
                for env_p in [_PROJECT_ROOT / ".env", _PROJECT_ROOT.parent / ".env"]:
                    if env_p.exists():
                        load_dotenv(dotenv_path=env_p, override=True)
                load_dotenv(override=True)
                st.session_state.voice_client = VoiceClient()
                st.rerun()

    st.caption(f"Ref Date: **{settings.REFERENCE_DATE}**")

    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.conversation_id = f"session_{int(time.time())}"
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("📦 Order Verification Inspector")
    insp_oid = st.text_input("Order ID", value="89782837")
    insp_proof = st.text_input("Phone Last 4 / Pincode", value="", type="password")
    if st.button("Lookup Order", use_container_width=True):
        res = st.session_state.order_tool.lookup_order(insp_oid, verification_value=insp_proof)
        if res.get("verified"):
            st.success(f"Verified! Customer: {res.get('customer_first_name')}")
            st.json({
                "status": res.get("status"),
                "total_inr": res.get("total_inr"),
                "payment_method": res.get("payment_method"),
                "delivered_on": res.get("delivered_on"),
                "items": res.get("items")
            })
        elif res.get("verification_required"):
            st.warning("Identity verification required! Provide phone last 4 digits or pincode.")
        else:
            st.error("Verification failed or order not found.")


# Main Layout
st.header("🛒 ZentroMart Voice & Chat Support Assistant")
st.markdown(
    "Welcome to the official ZentroMart AI customer support agent. "
    "You can talk to the agent via voice or type your inquiry below."
)

col_chat, col_voice = st.columns([3, 2])

with col_voice:
    st.subheader("🎤 Voice Interaction")
    audio_file = st.file_uploader("Upload Customer Audio (.wav)", type=["wav", "mp3"])
    
    use_mock_audio = st.button("🎵 Generate Demo Audio Query", help="Simulate customer voice note")
    
    if use_mock_audio or audio_file:
        with st.spinner("Processing speech via Gnani.ai STT..."):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
                if audio_file:
                    tmp_in.write(audio_file.read())
                else:
                    tmp_in.write(generate_mock_wav(duration_sec=1.5))
                in_path = tmp_in.name

            out_audio_path = Path(tempfile.gettempdir()) / f"reply_{int(time.time())}.wav"
            
            turn_res = st.session_state.voice_client.voice_turn(
                audio_path=in_path,
                agent=st.session_state.agent,
                conversation_id=st.session_state.conversation_id,
                language_code=lang_code,
                output_file=out_audio_path
            )
            
            # Record turn in chat history
            st.session_state.messages.append({
                "role": "user",
                "content": f"🎙️ [Voice]: {turn_res['heard']}",
                "sources": []
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": turn_res["reply"],
                "sources": turn_res.get("source_chunks", []),
                "audio_file": str(out_audio_path),
                "latencies": turn_res.get("latencies", {})
            })
            
            st.success("Spoken reply synthesized!")
            st.audio(str(out_audio_path), format="audio/wav")
            st.metric("Total Voice Latency", f"{turn_res['latencies']['total_ms']} ms")
            
            if os.path.exists(in_path):
                os.remove(in_path)

with col_chat:
    st.subheader("💬 Conversation")
    
    # Render messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("audio_file") and os.path.exists(msg["audio_file"]):
                st.audio(msg["audio_file"], format="audio/wav")
            if msg.get("sources"):
                st.caption(f"📚 **Grounded Sources:** {', '.join(msg['sources'])}")
            if msg.get("latencies"):
                l = msg["latencies"]
                st.caption(f"⏱️ STT: {l.get('stt_ms')}ms | Agent: {l.get('agent_ms')}ms | TTS: {l.get('tts_ms')}ms")

    # Text Input
    if user_input := st.chat_input("Type your message here (e.g. 'Hello', 'Where is my order 8978 2837?')..."):
        st.session_state.messages.append({"role": "user", "content": user_input, "sources": []})
        
        with st.spinner("Agent is reasoning..."):
            agent_res = st.session_state.agent.respond(
                message=user_input,
                conversation_id=st.session_state.conversation_id,
                step_mode=step_mode
            )
            
            # Synthesize reply for voice playback
            reply_wav = Path(tempfile.gettempdir()) / f"tts_{int(time.time())}.wav"
            _, tts_info = st.session_state.voice_client.synthesize(
                agent_res["reply"],
                language=lang_code,
                output_file=reply_wav
            )
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": agent_res["reply"],
                "sources": agent_res.get("source_chunks", []),
                "audio_file": str(reply_wav) if reply_wav.exists() else None,
                "latencies": {"tts_ms": tts_info.get("latency_ms", 0)}
            })
        st.rerun()
