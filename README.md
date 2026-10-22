# VoiceOps 2026: AI Customer Support Voice Agent
**LLM & Generative AI Course Capstone · Consulting & Analytics Club, IIT Guwahati × Gnani.ai**

An enterprise-grade, grounded customer support voice agent built for **ZentroMart** (a fictional Indian e-commerce store retailing groceries and electronics). The system listens to customer calls via **Gnani.ai Speech-to-Text**, reasons across 21 company policy documents and a 70-product catalog using **Retrieval-Augmented Generation (RAG)**, executes secure caller identity-gated database operations, manages conversation memory with coreference resolution, and replies with natural speech using **Gnani.ai Text-to-Speech**.

---

## 🌟 Key Features

1. **Grounded Document RAG Engine**:
   - Indexes 21 policy, agent guide, help, FAQ, and marketing documents.
   - Enforces strict legal precedence (**Policy > Agent Guide > Help > FAQ > Marketing**).
   - Downweights superseded policies (`pol_returns_v3_superseded.md`) in favor of active standards (`pol_returns_v4.md`).
   - Grounded product catalog lookups (`products.csv:<sku>`).
   - Zero hallucination guardrail: explicit refusal on unsupported questions ("I don't have information about that...").

2. **Identity-Gated Tool Calling (`tools.py`)**:
   - `lookup_order(order_id, verification_value=None)`: Caller identity gate requiring the last 4 digits of registered phone or 6-digit delivery pincode before revealing private details.
   - `create_ticket(summary, order_id, reason, intent)`: Escalation ticket logging for high-value claims (> ₹10,000) and human handovers.

3. **Multi-Turn Conversation Memory**:
   - Context maintenance and coreference tracking across turns.
   - Strict cross-customer session isolation (0% data leakage).
   - Business day timeline calculation adhering to the frozen reference date **20 October 2026** and skipping warehouse holidays.

4. **Gnani.ai Voice Integration**:
   - STT REST: Transcribes audio clips up to 60 seconds (supports `en-IN`, `hi-IN`, Hinglish).
   - TTS REST: High-fidelity speech synthesis using `timbre-v2.5` with voice `Kaveri`.
   - Text Normalizer: Spaced order IDs (`8 9 7 8, 2 8 3 7`), currency expansion, and 4-digit years.

5. **Multi-Interface Support**:
   - **FastAPI Backend**: Typed REST endpoints (`/health`, `/chat`, `/voice/respond`, `/orders/{id}`, `/tickets`).
   - **Streamlit Web UI**: Interactive voice recorder, live transcription, audio player, and order inspector.
   - **Batch Audio CLI (`run.py`)**: Official one-command batch runner for audio folders.

---

## 📊 Empirical Benchmark Results

Evaluated against the official practice datasets (`practice/questions.csv` and `practice/conversations.csv`):

| Evaluation Step | Evaluation Metric | Result | Benchmark Standard |
|---|---|---|---|
| **Step 1 Baseline** | Prompt-Only Accuracy | **11.54%** (6/52) | Unassisted LLM guesswork |
| **Step 2 RAG** | Grounded Answer Accuracy | **84.62%** (44/52) | **+73.08% Lift over Baseline** |
| **Step 2 RAG** | Knowledge Retrieval Hit Rate | **75.00%** (39/52) | Gold evidence chunk retrieval |
| **Step 3 Agent** | Conversation Decision Accuracy | **88.54%** (85/96) | Expected turn decisions |
| **Step 3 Agent** | Database Tool Calling Accuracy | **94.79%** (91/96) | Correct lookup and ticket calls |
| **Step 3 Agent** | Multi-Turn Conversation Turn Pass | **70.83%** (68/96) | Content & constraint compliance |
| **Step 4 Voice** | Batch Audio Turn Completion | **100.0%** | Full audio-to-speech loop |
| **System Health** | Automated PyTest Suite | **29/29 PASS** (100%) | Full test coverage |

---

## 🚀 Quickstart Guide

### 1. Installation
Clone repository and install dependencies:
```bash
git clone https://github.com/your-username/voiceops-2026.git
cd voiceops-2026
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Set your Gnani.ai API key (from [app.gnani.ai/voice](https://app.gnani.ai/voice)):
```env
GNANI_API_KEY=your_gnani_api_key_here
```
*(If no API key is set, the system seamlessly operates in offline mock speech mode for unit testing and local benchmarking).*

### 3. Initialize SQLite Database
Ingest all 7 CSV tables:
```bash
python scripts/ingest_data.py
```

---

## 💻 Running the System

### Option A: Official Batch Audio Runner (`run.py`)
Run the agent over a directory of customer voice recordings:
```bash
python run.py --input-dir data/sample_audios --output-dir sample_outputs
```
Generates text transcripts, synthesized WAV audio replies, and document citations in `sample_outputs/`.

### Option B: Interactive Streamlit Web Interface
Launch the web dashboard:
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) to record audio or type inquiries.

### Option C: FastAPI REST API
Start the backend server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Automated Testing & Evaluation

### Run Test Suite (29 Tests)
```bash
pytest tests/ -v
```

### Run Benchmark Comparison (Step 1 vs Step 2 vs Step 3)
```bash
python -m scripts.evaluate_agent
```

---

## 📁 Repository Structure

```text
voiceops-2026/
├── app/
│   ├── main.py                  # FastAPI application entrypoint
│   ├── config.py                # Pydantic configuration & settings
│   ├── api/                     # REST API routers (chat, voice, orders, health)
│   ├── agent/                   # Agent orchestrator, memory, policy rules, prompts
│   ├── tools/                   # Identity-gated order lookup & ticket creation tools
│   ├── rag/                     # Document loader, hybrid retriever, RAG engine
│   ├── voice/                   # Gnani STT/TTS client wrapper, text normalizer
│   ├── database/                # SQLite connection, DDL models, ingestion repository
│   └── schemas/                 # Pydantic request & response models
├── frontend/
│   └── app.py                   # Streamlit voice & chat web application
├── scripts/
│   ├── ingest_data.py           # Database ingestion CLI
│   ├── inspect_dataset.py       # Dataset audit script
│   ├── evaluate_agent.py        # 52 questions & 96 turns benchmark script
│   └── generate_report_pdf.py   # PDF report generator
├── tests/
│   ├── test_database.py         # DB counts & order math tests
│   ├── test_rag.py              # Retrieval & precedence tests
│   ├── test_tools.py            # Caller verification gate tests
│   ├── test_agent.py            # Multi-turn conversation & isolation tests
│   ├── test_voice.py            # Voice normalizer & pipeline tests
│   └── test_api.py              # FastAPI endpoint tests
├── data/                        # SQLite database & audio cache
├── sample_outputs/              # Batch audio execution outputs
├── reports/                     # Benchmark results JSON
├── run.py                       # Mandatory batch runner script
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
├── README.md                    # Main documentation
├── REQUIREMENTS.md              # Extracted requirements specification
├── DATASET_AUDIT.md             # Dataset audit & schema analysis
├── IMPLEMENTATION_PLAN.md       # Implementation blueprint
├── ARCHITECTURE.md              # System design & sequence diagrams
├── EVALUATION_REPORT.md         # Full benchmark evaluation report
├── SETUP_GUIDE.md               # Detailed installation & usage guide
├── DEMO_SCRIPT.md               # 2-minute video demo script
├── SUBMISSION_CHECKLIST.md      # Final deliverable verification checklist
└── report.pdf                   # Official 4-page summary report
```

---

## 👥 Authors
Built for the **VoiceOps 2026 Capstone Project** by Team ZentroMart.
Consulting & Analytics Club, IIT Guwahati × Gnani.ai.
