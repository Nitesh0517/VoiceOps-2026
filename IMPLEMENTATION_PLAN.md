# VoiceOps 2026 — Implementation Plan

## 1. Architecture Overview

```
                                  [ Customer Audio / Text ]
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
             [ Gnani STT API ]                                 [ Text Query ]
             (transcribe: en/hi)                                      │
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              ▼
                             [ VoiceOps Orchestration Agent ]
                             (Context Memory & Coreference)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
          [ RAG Knowledge Base ]      [ Database Tools ]      [ Verification Gate ]
          - 21 Documents Indexed      - lookup_order          - Phone last 4 digits
          - Precedence Re-ranking     - create_ticket         - Delivery pincode
          - Section ID Citations      - SQLite Database       - Max 1 retry rule
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                   [ Grounded LLM Response ]
                               (Text Normalization for Speech)
                                              │
                                              ▼
                                     [ Gnani TTS API ]
                                (synthesize: timbre-v2.5)
                                              │
                                              ▼
                                     [ Audio Response ]
```

---

## 2. Directory Layout & Module Plan

```text
c:\Users\nites\Desktop\VOICE\
├── app/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings, environment variables, reference date
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py         # SQLite connection manager & thread-safe sessions
│   │   ├── models.py             # SQLite table definitions & schemas
│   │   ├── repository.py         # Query helpers for orders, customers, items, products, pincodes
│   │   └── ingest.py             # Data ingestion pipeline from CSV to SQLite
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── document_loader.py    # Parses 21 kb/*.md, extracts frontmatter & [SECTION-ID]
│   │   ├── chunker.py            # Section-aware chunking preserving metadata
│   │   ├── retriever.py          # Hybrid BM25/TF-IDF + dense semantic retriever
│   │   ├── precedence.py         # Document precedence filter & reranker
│   │   └── rag_engine.py         # Grounded prompt construction & citation tracker
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py               # Tool registry & execution interface
│   │   ├── order_tool.py         # Identity-gated order lookup
│   │   ├── ticket_tool.py        # Escalation ticket creation
│   │   └── policy_tool.py        # Direct policy retrieval tool
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── memory.py             # Multi-turn conversation state & coreference tracker
│   │   ├── prompts.py            # System prompts (Step 1 baseline vs Step 3 agent)
│   │   ├── policy_rules.py       # Deterministic business rules (business days, damage limits)
│   │   ├── llm_client.py         # Multi-backend LLM client (Gemini, OpenAI, Offline fallback)
│   │   └── orchestrator.py       # Main agent coordinating memory, tools, RAG, and LLM
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── gnani_client.py       # Gnani STT and TTS client wrapper with error handling
│   │   ├── normalizer.py         # Speech text normalizer (spelled order IDs, explicit years)
│   │   └── mock_speech.py        # Test speech synthesizer & transcription simulator
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py               # Pydantic chat request/response models
│   │   ├── voice.py              # Pydantic voice request/response models
│   │   └── tools.py              # Tool call parameter schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_chat.py        # /chat endpoint
│   │   ├── routes_voice.py       # /voice/transcribe, /voice/respond endpoints
│   │   ├── routes_orders.py      # /orders/{order_id} lookup endpoint
│   │   └── routes_health.py      # /health endpoint
│   └── main.py                   # FastAPI application factory & lifespan
├── frontend/
│   └── app.py                    # Streamlit interface (voice, chat, history, tool logs)
├── scripts/
│   ├── inspect_dataset.py        # Dataset summary script
│   ├── ingest_data.py            # SQLite ingestion CLI
│   └── evaluate_agent.py         # Full benchmarking suite for Step 1 vs Step 2 vs Step 3
├── tests/
│   ├── test_dataset.py           # Integrity and schema tests
│   ├── test_database.py          # SQLite database & repository tests
│   ├── test_rag.py               # Retrieval quality & precedence tests
│   ├── test_tools.py             # Tool execution & identity verification gates
│   ├── test_agent.py             # Multi-turn conversation & coreference tests
│   ├── test_voice.py             # Voice STT/TTS normalization & pipeline tests
│   └── test_api.py               # FastAPI endpoint tests
├── run.py                        # Mandatory batch runner: run.py --input-dir ... --output-dir ...
├── requirements.txt
├── .env.example
├── README.md
├── REQUIREMENTS.md
├── DATASET_AUDIT.md
├── IMPLEMENTATION_PLAN.md
├── ARCHITECTURE.md
├── EVALUATION_REPORT.md
└── SETUP_GUIDE.md
```

---

## 3. Step-by-Step Execution Phases

### Phase 2: Data Ingestion & Database (`app/database/`)
1. Create SQLite schema matching `data/*.csv` with relational integrity.
2. Build repeatable ingestion script `app/database/ingest.py` loading `customers`, `orders`, `order_items`, `products`, `pincodes`, `holidays`, `support_logs`.
3. Verify data integrity against `validate_dataset.py`.

### Phase 3: RAG Knowledge Base (`app/rag/`)
1. Markdown parser extracting YAML frontmatter (`doc_id`, `doc_type`, `effective_from`, `status`) and section headings `## [SECTION-ID]`.
2. Construct hybrid retrieval index (BM25 + TF-IDF character/word n-grams for Hindi/English + cosine vector similarity).
3. Implement document precedence filter (`KB-00.1`): `policy` > `agent_guide` > `help` > `faq` > `marketing`.
4. Implement catalog grounding for product queries (`products.csv:<sku>`).
5. Add confidence threshold to trigger explicit refusal ("Sorry, I don't have information about that...").

### Phase 4 & 5: AI Agent, Tools, and Conversation Memory (`app/agent/`, `app/tools/`)
1. Tool implementation wrapping verified order lookup and ticket generation.
2. Caller verification finite state machine (Unverified $\to$ Pending Verification $\to$ Verified / Denied).
3. Conversation memory class managing session state, coreference resolution (e.g. "same item", "it", "that order"), and turn history.
4. Business day timeline calculator respecting 2026-10-20 reference date and warehouse holidays.
5. Dual prompt design: Step 1 (unassisted baseline) vs Step 3 (full grounded agent with tools).

### Phase 6: Gnani.ai Voice Integration (`app/voice/`)
1. Wrap `GnaniSTTClient` for audio transcription with language code support (`en-IN`, `hi-IN`).
2. Wrap `GnaniTTSClient` for speech synthesis (`voice="Kaveri"`, `model="timbre-v2.5"`).
3. Text normalization for the ear: spell out order IDs ("8 9 7 8 2 8 3 7"), expand abbreviations, include 4-digit years in dates.
4. Robust fallback handling if credentials are not configured, with synthetic audio generation for unit tests.

### Phase 7: FastAPI Backend (`app/api/`, `app/main.py`)
1. Fast, typed endpoints: `/health`, `/chat`, `/voice/transcribe`, `/voice/respond`, `/orders/{order_id}`, `/tickets`.
2. Pydantic input validation, CORS middleware, structured error responses.

### Phase 8: Frontend UI (`frontend/app.py`)
1. Streamlit web application with:
   - Voice audio recording and file upload.
   - Live transcription display.
   - Assistant speech playback.
   - Multi-turn conversation view with session switcher.
   - Interactive order lookup and ticket tracker.

### Phase 9: Evaluation Suite & Benchmark Run (`scripts/evaluate_agent.py`)
1. Benchmark Step 1 (Prompt-only baseline) on 52 practice questions.
2. Benchmark Step 2 (RAG grounded) on 52 practice questions (Decision accuracy, Hit@K, MRR, must_include/must_not_include compliance).
3. Benchmark Step 3 on 23 practice conversations (96 turns) testing verification gates and coreference.
4. Generate `EVALUATION_REPORT.md` with empirical scores and error analysis.

### Phase 10: PyTest Suite & Mandatory Batch Runner (`run.py`)
1. Comprehensive automated test suite (`tests/`) covering all subsystems.
2. Implement `run.py` supporting batch directory execution: `python run.py --input-dir <audio_dir> --output-dir <out_dir>`.
3. Complete final documentation (`README.md`, `SETUP_GUIDE.md`, `ARCHITECTURE.md`).
