"""Streamlit UI for VoiceOps 2026 — ZentroMart AI Customer Support Voice Agent.

A modern, professional dashboard with evaluation mode routing, live Gnani.ai voice,
grounded RAG citations, and caller identity verification.
"""
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

# Explicitly load .env from the project root into environment on every run
from dotenv import load_dotenv
_env_file = _PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(dotenv_path=_env_file, override=True)
load_dotenv(override=True)

import streamlit as st
import pandas as pd
from app.config import settings, reload_settings_env
from app.agent.orchestrator import VoiceOpsAgent
from app.voice.gnani_client import VoiceClient
from app.voice.mock_speech import generate_mock_wav
from app.tools.order_tool import OrderTool
from app.tools.ticket_tool import TicketTool

st.set_page_config(
    page_title="VoiceOps 2026 — ZentroMart Support Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling, cards, and visual hierarchy
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 0.35rem;
        margin-bottom: 0;
    }
    .mode-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .mode-pill {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        margin-right: 0.4rem;
        margin-bottom: 0.3rem;
    }
    .pill-green { background-color: #dcfce7; color: #166534; }
    .pill-blue { background-color: #dbeafe; color: #1e40af; }
    .pill-purple { background-color: #f3e8ff; color: #6b21a8; }
    .pill-amber { background-color: #fef3c7; color: #92400e; }
    .pill-red { background-color: #fee2e2; color: #991b1b; }
    
    .pipeline-step {
        text-align: center;
        background: #f1f5f9;
        border-radius: 8px;
        padding: 0.6rem 0.4rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
    }
    .metric-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        text-align: center;
    }
    .metric-title {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = f"session_3_{int(time.time())}"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = VoiceOpsAgent()
if "current_step_mode" not in st.session_state:
    st.session_state.current_step_mode = 3

# Resilient VoiceClient loading: auto-upgrades to live if GNANI_API_KEY is present
active_key = (os.getenv("GNANI_API_KEY", "").strip() or getattr(settings, "GNANI_API_KEY", "").strip())
if ("voice_client" not in st.session_state
        or (active_key and not st.session_state.voice_client.is_live)
        or (not active_key and st.session_state.voice_client.is_live)):
    st.session_state.voice_client = VoiceClient()

if "order_tool" not in st.session_state:
    st.session_state.order_tool = OrderTool()
if "ticket_tool" not in st.session_state:
    st.session_state.ticket_tool = TicketTool()

# ==========================================
# SIDEBAR: CONFIGURATION, SPEECH & INSPECTOR
# ==========================================
with st.sidebar:
    st.title("🎙️ VoiceOps 2026")
    st.caption("IIT Guwahati × Gnani.ai Capstone Project")
    st.divider()

    # 1. EVALUATION MODE SELECTOR
    st.subheader("⚙️ Evaluation Mode")
    
    mode_options = [3, 2, 1]
    mode_labels = {
        3: "Step 3: Full Agent (Production)",
        2: "Step 2: RAG Grounded Q&A",
        1: "Step 1: Baseline Prompt-Only"
    }
    
    selected_step = st.radio(
        "Select Active Pipeline Step:",
        options=mode_options,
        index=mode_options.index(st.session_state.current_step_mode),
        format_func=lambda x: mode_labels[x],
        help="Controls whether the agent uses full memory & tools (Step 3), document-only RAG (Step 2), or raw prompt-only LLM (Step 1)."
    )

    # Detect mode change and safely manage conversation context
    if selected_step != st.session_state.current_step_mode:
        prev_step = st.session_state.current_step_mode
        st.session_state.current_step_mode = selected_step
        # Reset conversation to avoid context corruption between incompatible modes
        st.session_state.conversation_id = f"session_{selected_step}_{int(time.time())}"
        st.session_state.messages = []
        st.toast(f"Switched from Step {prev_step} to Step {selected_step}. Started fresh session.", icon="🔄")
        st.rerun()

    # Mode Explanatory Card
    if selected_step == 3:
        st.markdown("""
        <div class="mode-card">
            <span class="mode-pill pill-green">Active: Step 3</span>
            <span class="mode-pill pill-purple">Multi-Turn Memory</span>
            <span class="mode-pill pill-blue">Identity Gating</span>
            <span class="mode-pill pill-amber">Support Tools</span>
            <p style="font-size: 0.85rem; color: #475569; margin-top: 0.5rem; margin-bottom: 0;">
                <strong>Full Production Agent:</strong> Maintains conversation state across turns, enforces registered phone/pincode verification before exposing order details, executes database lookups, and escalates high-value claims to human support.
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif selected_step == 2:
        st.markdown("""
        <div class="mode-card">
            <span class="mode-pill pill-blue">Active: Step 2</span>
            <span class="mode-pill pill-green">Hybrid RAG</span>
            <span class="mode-pill pill-amber">Precedence Rules</span>
            <span class="mode-pill pill-red">No Tools</span>
            <p style="font-size: 0.85rem; color: #475569; margin-top: 0.5rem; margin-bottom: 0;">
                <strong>Grounded Knowledge Base Q&A:</strong> Evaluates single-turn document retrieval. Answers strictly from official ZentroMart policy documents and returns <em>"I don't know"</em> when unsupported. No memory or tools.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mode-card">
            <span class="mode-pill pill-red">Active: Step 1</span>
            <span class="mode-pill pill-amber">Prompt-Only</span>
            <span class="mode-pill pill-red">No RAG</span>
            <span class="mode-pill pill-red">No Tools</span>
            <p style="font-size: 0.85rem; color: #475569; margin-top: 0.5rem; margin-bottom: 0;">
                <strong>Baseline Comparison:</strong> Raw LLM prompt-only baseline without company documents or tools. Demonstrates the ungrounded baseline for rubric comparison (11.5% accuracy vs 84.6% in Step 2).
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Language Selector
    lang_code = st.selectbox(
        "🗣️ Speech & Response Language",
        options=["en-IN", "hi-IN"],
        format_func=lambda x: "English (India) — en-IN" if x == "en-IN" else "Hindi (हिन्दी) — hi-IN"
    )

    st.divider()

    # 2. GNANI.AI SPEECH API STATUS
    st.subheader("🔑 Gnani.ai Speech Engine")
    
    if st.session_state.voice_client.is_live:
        st.success("🟢 **Live REST API Connected**")
        st.caption("TTS Model: `timbre-v2.5` | Voice: `Kaveri`")
        if st.button("🔌 Test API Connection", use_container_width=True):
            with st.spinner("Pinging Gnani.ai API..."):
                test_res = st.session_state.voice_client.test_connection()
                if test_res["status"] == "success":
                    st.success(test_res["message"])
                else:
                    st.error(test_res["message"])
    else:
        st.warning("🟠 **Offline Mock Engine (No Key)**")
        with st.expander("ℹ️ How to enable Live Voice"):
            st.markdown(
                "1. Get API key from [app.gnani.ai/voice](https://app.gnani.ai/voice)\n"
                "2. Add to `.env` in project root:\n"
                "   ```env\n"
                "   GNANI_API_KEY=your_key_here\n"
                "   ```\n"
                "3. Click **Reload Credentials** below:"
            )

    if st.button("🔄 Reload Credentials", use_container_width=True):
        for env_p in [_PROJECT_ROOT / ".env", _PROJECT_ROOT.parent / ".env"]:
            if env_p.exists():
                load_dotenv(dotenv_path=env_p, override=True)
        load_dotenv(override=True)
        reload_settings_env()
        st.session_state.voice_client = VoiceClient()
        st.rerun()

    st.caption(f"Policy Reference Date: **{settings.REFERENCE_DATE}**")

    if st.button("🧹 Reset Conversation", use_container_width=True):
        st.session_state.conversation_id = f"session_{st.session_state.current_step_mode}_{int(time.time())}"
        st.session_state.messages = []
        st.toast("Conversation session cleared.", icon="🧹")
        st.rerun()

    st.divider()

    # 3. ORDER IDENTITY VERIFICATION INSPECTOR
    st.subheader("📦 Order Verification Inspector")
    st.caption("Direct verification gate test (Caller privacy protection)")
    insp_oid = st.text_input("Order ID", value="89782837", help="8-digit synthetic order number")
    insp_proof = st.text_input("Phone Last 4 OR Pincode", value="", type="password", help="Enter phone last 4 (e.g. 4533) or delivery pincode (e.g. 781006)")
    
    if st.button("Inspect Order Record", use_container_width=True):
        res = st.session_state.order_tool.lookup_order(insp_oid, verification_value=insp_proof)
        if res.get("verified"):
            st.success(f"Identity Verified! Customer: {res.get('customer_first_name')}")
            st.json({
                "order_id": res.get("order_id"),
                "status": res.get("status"),
                "total_inr": res.get("total_inr"),
                "payment_method": res.get("payment_method"),
                "delivered_on": res.get("delivered_on"),
                "items": res.get("items")
            })
        elif res.get("verification_required"):
            st.warning("⚠️ Identity verification required! Provide registered phone's last 4 digits OR delivery pincode.")
        else:
            st.error("❌ Verification failed or order not found.")


# ==========================================
# MAIN DASHBOARD LAYOUT
# ==========================================

# Header Banner
st.markdown(f"""
<div class="main-header">
    <h1>🛒 ZentroMart AI Customer Support Voice Agent</h1>
    <p>VoiceOps 2026 Capstone • Reference Date: <strong>{settings.REFERENCE_DATE}</strong> • Current Mode: <strong>{mode_labels[st.session_state.current_step_mode]}</strong></p>
</div>
""", unsafe_allow_html=True)

# Processing Pipeline Flow Display
col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
with col_p1:
    st.markdown('<div class="pipeline-step">1. Customer Audio</div>', unsafe_allow_html=True)
with col_p2:
    st.markdown('<div class="pipeline-step">2. Gnani STT</div>', unsafe_allow_html=True)
with col_p3:
    st.markdown(f'<div class="pipeline-step">3. Agent (Step {st.session_state.current_step_mode})</div>', unsafe_allow_html=True)
with col_p4:
    st.markdown('<div class="pipeline-step">4. Gnani TTS</div>', unsafe_allow_html=True)
with col_p5:
    st.markdown('<div class="pipeline-step">5. Spoken Reply</div>', unsafe_allow_html=True)

st.write("")

# 2-Column Responsive Dashboard Layout
col_chat, col_voice = st.columns([3, 2], gap="large")

# ------------------------------------------
# COLUMN 1: CHAT CONVERSATION
# ------------------------------------------
with col_chat:
    st.subheader("💬 Customer Conversation")
    
    # Active mode indicator badge
    mode_badges = {
        3: '<span class="mode-pill pill-green">Step 3: Full Agent</span> <span style="font-size: 0.8rem; color: #64748b;">Memory + Tools + Caller Verification Active</span>',
        2: '<span class="mode-pill pill-blue">Step 2: RAG Q&A</span> <span style="font-size: 0.8rem; color: #64748b;">Knowledge Base Retrieval Only</span>',
        1: '<span class="mode-pill pill-red">Step 1: Baseline</span> <span style="font-size: 0.8rem; color: #64748b;">Ungrounded Prompt-Only</span>'
    }
    st.markdown(mode_badges[st.session_state.current_step_mode], unsafe_allow_html=True)
    st.write("")

    # Chat Message Thread
    if not st.session_state.messages:
        st.info("👋 Start the conversation by speaking below, uploading customer audio, or typing a query (e.g. *'Hello, I need help with my order 8978 2837'* or *'What is your return policy for electronics?'*).")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Inline audio player if available
            if msg.get("audio_file") and os.path.exists(msg["audio_file"]):
                st.audio(msg["audio_file"], format="audio/wav")
            
            # Grounded citations
            if msg.get("sources"):
                sources_str = ", ".join([f"`{s}`" for s in msg["sources"]])
                st.caption(f"📚 **Grounded Sources:** {sources_str}")
                
            # Tool calls executed
            if msg.get("tool_calls"):
                tools_str = ", ".join([f"`{t}`" for t in msg["tool_calls"]])
                st.caption(f"⚙️ **Tools Executed:** {tools_str}")
                
            # Turn Latencies
            if msg.get("latencies"):
                l = msg["latencies"]
                st.caption(f"⏱️ **Latency:** STT: {l.get('stt_ms', 0)}ms | Agent: {l.get('agent_ms', 0)}ms | TTS: {l.get('tts_ms', 0)}ms | Total: {l.get('total_ms', l.get('tts_ms', 0))}ms")

    # Quick Suggestion Pills
    st.write("")
    st.caption("Quick inquiry prompts:")
    q_col1, q_col2, q_col3 = st.columns(3)
    prompt_selected = None
    with q_col1:
        if st.button("📦 Track Order 8978 2837", use_container_width=True):
            prompt_selected = "Hello, I need help with my order 8978 2837."
    with q_col2:
        if st.button("🔄 Return Policy", use_container_width=True):
            prompt_selected = "What is the return window for electronics?"
    with q_col3:
        if st.button("⚡ Express Delivery Late", use_container_width=True):
            prompt_selected = "My express delivery was late. Do I get the fee back?"

    # Chat Input Box
    user_input = st.chat_input("Type your message here (e.g. 'Hello', 'My phone ends with 4533')...")
    active_prompt = user_input or prompt_selected

    if active_prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": active_prompt,
            "sources": []
        })
        
        with st.spinner("Agent is reasoning..."):
            agent_res = st.session_state.agent.respond(
                message=active_prompt,
                conversation_id=st.session_state.conversation_id,
                step_mode=st.session_state.current_step_mode
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
                "tool_calls": agent_res.get("tool_calls", []),
                "audio_file": str(reply_wav) if reply_wav.exists() else None,
                "latencies": {"tts_ms": tts_info.get("latency_ms", 0)}
            })
        st.rerun()

# ------------------------------------------
# COLUMN 2: VOICE CONSOLE & PERFORMANCE
# ------------------------------------------
with col_voice:
    st.subheader("🎤 Voice Interaction Console")
    
    st.markdown("""
    Upload a customer audio file or simulate customer speech. Audio is transcribed via **Gnani STT**, reasoned by the **ZentroMart Agent**, and synthesized back via **Gnani TTS**.
    """)

    audio_file = st.file_uploader("Upload Customer Voice Note (.wav, .mp3)", type=["wav", "mp3"])
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        use_demo_order = st.button("🎵 Demo: Order Status Query", help="Simulate voice asking about order 8978 2837", use_container_width=True)
    with c_btn2:
        use_demo_policy = st.button("🎵 Demo: Return Policy Query", help="Simulate voice asking about return policy", use_container_width=True)
    
    selected_demo_audio = None
    if use_demo_order:
        selected_demo_audio = _PROJECT_ROOT / "data" / "sample_audios" / "sample_customer_order_help.wav"
    elif use_demo_policy:
        selected_demo_audio = _PROJECT_ROOT / "data" / "sample_audios" / "sample_customer_return_query.wav"

    if audio_file or selected_demo_audio:
        with st.spinner("Processing speech through Gnani Voice Pipeline..."):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
                if audio_file:
                    tmp_in.write(audio_file.read())
                elif selected_demo_audio and selected_demo_audio.exists():
                    tmp_in.write(selected_demo_audio.read_bytes())
                else:
                    tmp_in.write(generate_mock_wav(duration_sec=1.5))
                in_path = tmp_in.name

            out_audio_path = Path(tempfile.gettempdir()) / f"voice_turn_reply_{int(time.time())}.wav"
            
            turn_res = st.session_state.voice_client.voice_turn(
                audio_path=in_path,
                agent=st.session_state.agent,
                conversation_id=st.session_state.conversation_id,
                language_code=lang_code,
                output_file=out_audio_path,
                step_mode=st.session_state.current_step_mode
            )
            
            # Record turn in chat history
            st.session_state.messages.append({
                "role": "user",
                "content": f"🎙️ [Customer Voice]: {turn_res['heard']}",
                "sources": []
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": turn_res["reply"],
                "sources": turn_res.get("source_chunks", []),
                "tool_calls": turn_res.get("tool_calls", []),
                "audio_file": str(out_audio_path),
                "latencies": turn_res.get("latencies", {})
            })
            
            if os.path.exists(in_path):
                os.remove(in_path)

            st.success("✅ Complete Voice Turn Processed!")
            
            # Performance Metric Cards
            l = turn_res.get("latencies", {})
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'<div class="metric-box"><div class="metric-title">STT</div><div class="metric-value">{l.get("stt_ms", 0)}ms</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-box"><div class="metric-title">Agent</div><div class="metric-value">{l.get("agent_ms", 0)}ms</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-box"><div class="metric-title">TTS</div><div class="metric-value">{l.get("tts_ms", 0)}ms</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-box"><div class="metric-title">Total</div><div class="metric-value">{l.get("total_ms", 0)}ms</div></div>', unsafe_allow_html=True)

            st.write("")
            st.write("**Synthesized Audio Response:**")
            st.audio(str(out_audio_path), format="audio/wav")

    st.divider()

    # Evaluation Benchmark Overview
    st.subheader("📊 Capstone Benchmark Comparison")
    st.caption("Empirical benchmark results frozen on reference date 2026-10-20:")
    
    st.markdown("""
    | Step | Pipeline Mode | Accuracy | Status |
    |---|---|---|---|
    | **Step 1** | Baseline Prompt-Only | **11.54%** | Ungrounded Guesswork |
    | **Step 2** | Grounded RAG Q&A | **84.62%** | **+73.08% Lift** |
    | **Step 3** | Full Conversational Agent | **88.54%** | Multi-Turn & Verification |
    """)
