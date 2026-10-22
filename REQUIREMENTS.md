# VoiceOps 2026 — Requirements Specification

## 1. Executive Summary & Problem Statement
* **Company**: ZentroMart (fictional Indian online retail store selling groceries and electronics).
* **Reference Date**: **20 October 2026** (all deadline, return window, and delay calculations must be evaluated relative to this date).
* **Business Problem**: ZentroMart customer support receives thousands of inquiries daily covering order tracking, returns, refund timelines, damaged/wrong deliveries, cancellation eligibility, and warranty claims. Most customers prefer calling over typing, and communicate in English, Hindi, and Hinglish.
* **Objective**: Build an end-to-end AI-powered customer support voice agent that:
  1. Accurately answers inquiries strictly grounded in official company policies, catalogs, and FAQs.
  2. Executes verified order lookups and logs escalation tickets using database-backed tools.
  3. Maintains multi-turn context memory and coreference resolution while preventing cross-customer data leakage.
  4. Integrates Gnani.ai STT (`GnaniSTTClient`) and TTS (`GnaniTTSClient`) for speech interaction in Indian languages (English, Hindi, Hinglish).
  5. Distinguishes between answerable queries, customer-specific lookups, and unsupported questions (responding "I don't have information about that..." and offering human handover).

---

## 2. Four-Step Project Architecture (Course Alignment)

| Step | Focus Area | Key Requirements | Evaluation Focus |
|---|---|---|---|
| **Step 1** | Prompt-Only LLM Baseline | System prompt establishing role as ZentroMart AI assistant. Introduces itself on first turn. No access to RAG knowledge base. Guesswork baseline. | Baseline correctness on practice questions |
| **Step 2** | Document Grounding (RAG) | Semantic retrieval over 21 `kb/*.md` files. Chunk preservation of `[SECTION-ID]`, `status`, `effective_from`. Strict precedence resolution. Refusal on unsupported questions. | Grounded answer accuracy (25 marks), Retrieval quality (15 marks), Step 1 vs Step 2 comparison (10 marks) |
| **Step 3** | Conversational Agent & Tools | Multi-turn memory, caller identity verification gate (last 4 digits of phone or 6-digit delivery pincode), `lookup_order`, `create_ticket`, policy escalation rules. | Multi-turn handling, coreference, verification security, ticket logging (20 marks) |
| **Step 4** | Voice Integration (Gnani.ai) | Customer Audio $\to$ Gnani STT REST $\to$ Agent Pipeline $\to$ Gnani TTS (`timbre-v2.5` / `voice="Kaveri"`) $\to$ Output Audio (`reply.wav`). | End-to-end voice flow (10 marks), Speech latency and naturalness (10 marks) |

---

## 3. Mandatory Technologies & APIs

* **Language**: Python 3.11+ (Python 3.14 compatible).
* **Speech-to-Text (STT)**: Gnani.ai STT REST API via `gnani-vachana` (`GnaniSTTClient`).
* **Text-to-Speech (TTS)**: Gnani.ai TTS REST API via `gnani-vachana` (`GnaniTTSClient`, model `timbre-v2.5` or `timbre-v3.0`).
* **LLM Engine**: Multi-provider support (Google Gemini `google-genai`, OpenAI `openai`, and deterministic offline neural/hybrid pipeline).
* **Database**: SQLite3 (`zentromart.db`) with parameterized queries and foreign key integrity.
* **Backend API**: FastAPI (`uvicorn`) with Pydantic request/response schemas, CORS, and comprehensive endpoints.
* **Frontend UI**: Streamlit web application supporting live audio recording/upload, STT transcript display, LLM response streaming, TTS playback, order lookup inspector, and ticket tracking.
* **Testing & Evaluation**: PyTest suite, automated evaluation script (`evaluate_agent.py`), batch execution script (`run.py`).

---

## 4. Knowledge Base & Document Precedence Rules

According to `kb/00_about_this_knowledge_base.md`:
1. **Policy Documents** (`pol_*.md`, `status: current`) — Highest authority.
   * `pol_returns_v4.md` overrides `pol_returns_v3_superseded.md`.
2. **Agent Guides** (`agent_*.md`) — Operational procedures, verification gates, escalation workflows.
3. **Help Articles** (`help_*.md`) — Step-by-step customer self-service guides.
4. **FAQs** (`faq_*.md`, `faq_hindi.md`) — Common question summaries (subordinate to policies; e.g. wallet refund is instant/2 hrs in policy vs 5-7 days in generic FAQ).
5. **Marketing Pages** (`mkt_*.md`) — Promotional statements (cannot override policies).
6. **Historical Support Logs** (`data/support_logs.csv`) — Context only; NOT policy authority.

---

## 5. Security & Verification Rules

* **Caller Verification Gate (`agent_identity_verification.md`)**:
  - Unverified `lookup_order(order_id)` MUST return `verification_required: True` and zero order/customer details.
  - Verification succeeds ONLY when caller provides:
    a) Last 4 digits of registered phone number, OR
    b) 6-digit delivery pincode.
  - Never disclose the expected verification value to the caller.
  - Max 1 retry permitted.
  - After verification passes, order status, items, tracking, and customer first name are unlocked for that conversation turn.
* **Cross-Customer Isolation**:
  - Conversations are strictly segregated by `conversation_id`.
  - No customer order details or verification tokens leak between sessions or in public logs.
* **Escalation Rules (`agent_escalation_handoff.md`)**:
  - High-value damage claims ($> ₹10,000$) require Priority Resolution review (`create_ticket`).
  - Compensation requests cannot be granted by the AI. Refuse politely and hand over to human agent.
  - Expired return windows cannot be overridden by the AI.

---

## 6. Official Evaluation Rubric (100 Marks)

1. **Correct, Grounded Answers (25 Marks)**: Document-grounded factual correctness, explicit refusal ("I don't know") when unsupported.
2. **Retrieval Quality (15 Marks)**: Precision and recall of retrieved section chunks matching `gold_evidence` and avoiding `hard_negatives`.
3. **Conversation Handling (20 Marks)**: Multi-turn continuity, clarifying questions, identity verification, proper refusal and handoffs.
4. **Own Evaluation & Comparison (10 Marks)**: Step 1 (prompt-only) vs Step 2 (RAG) benchmark metrics and empirical analysis.
5. **Voice End-to-End Execution (10 Marks)**: Audio file ingestion $\to$ STT $\to$ Agent $\to$ TTS audio output.
6. **Voice Experience (10 Marks)**: Short, conversational replies tailored for speech, text normalization (dates with years, spaced order IDs).
7. **Report & Deliverables (10 Marks)**: Comprehensive report, runnable batch script (`run.py`), clean repository structure.

---

## 7. Submission Artifacts
* Complete source code with modular architecture (`app/`, `tests/`, `scripts/`, `frontend/`).
* Batch execution script: `run.py --input-dir <audio_folder> --output-dir <results_folder>`.
* Automated test suite passing 100% of tests.
* `EVALUATION_REPORT.md` with real benchmark runs on 52 practice questions and 23 conversations (96 turns).
* `SETUP_GUIDE.md`, `ARCHITECTURE.md`, `README.md`, `.env.example`.
