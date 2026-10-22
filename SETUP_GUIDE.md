# VoiceOps 2026 — Setup & User Guide

## 1. System Requirements
* Python 3.11+ (Fully tested on Python 3.14.0)
* Operating System: Windows, macOS, or Linux
* Audio Support: 16kHz WAV recording/playback
* Gnani.ai API Key (from `app.gnani.ai/voice`) — optional for offline mode

---

## 2. Installation Steps

### Step 1: Clone the Repository & Enter Workspace
```bash
cd VOICE
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and optionally set your API keys:
```env
GNANI_API_KEY=your_gnani_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here  # Optional
OPENAI_API_KEY=your_openai_api_key_here  # Optional
```
> **Note**: If `GNANI_API_KEY` is omitted, the system automatically runs in high-fidelity mock audio mode for offline evaluation and unit tests.

---

## 3. Data Ingestion & Database Initialization
Ingest the 7 CSV datasets into the local SQLite database (`data/zentromart.db`):
```bash
python scripts/ingest_data.py
```
Expected output:
```
Ingesting ZentroMart datasets into SQLite...
Ingestion complete successfully!
  - pincodes: 36 rows
  - holidays: 4 rows
  - customers: 300 rows
  - products: 70 rows
  - orders: 1000 rows
  - order_items: 1783 rows
  - support_logs: 244 rows
```

To run offline validation on the extracted dataset:
```bash
cd Capstone_Project_Dataset_FTTT_2026
python validate_dataset.py
cd ..
```

---

## 4. Running the Application

### Option A: Start FastAPI Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation:
* [http://localhost:8000/docs](http://localhost:8000/docs)
* Health Endpoint: [http://localhost:8000/health](http://localhost:8000/health)

### Option B: Start Streamlit Frontend
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your web browser.

---

## 5. Official Batch Run Command (`run.py`)
To process a folder of customer audio files, transcribe them, run the agent, and output synthesized voice responses:

```bash
python run.py --input-dir data/sample_audios --output-dir sample_outputs
```

Output includes:
* `<file_stem>_reply.wav`: Synthesized audio response.
* `<file_stem>_result.json`: Grounded text response, citations, and latencies.
* `batch_summary.json`: Complete batch run summary.

---

## 6. Running Tests & Benchmarks

### Run Automated Unit & Integration Tests (29 Tests)
```bash
pytest tests/ -v
```

### Run Benchmark Suite (Step 1 vs Step 2 vs Step 3)
```bash
python -m scripts.evaluate_agent
```
Results and metrics are saved to `reports/evaluation_results.json`.
