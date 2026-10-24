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

### Step 3: Configure Environment Variables & Gnani.ai Credentials

1. **Obtain your Gnani API Key:**
   * Sign in to [app.gnani.ai/voice](https://app.gnani.ai/voice).
   * Generate an API key. A single key covers both Speech-to-Text (STT) and Text-to-Speech (TTS).

2. **Create your local `.env` file:**
   In Windows PowerShell:
   ```powershell
   Copy-Item .env.example .env
   ```
   Or in Bash:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and set your credentials:**
   ```env
   GNANI_API_KEY=your_actual_key_here
   GEMINI_API_KEY=your_gemini_api_key_here  # Optional: for live LLM generation
   OPENAI_API_KEY=your_openai_api_key_here  # Optional
   ```
   > ⚠️ **Important Security Note**: Never commit `.env` or share secret keys in public chats/repositories. The `.gitignore` file already ignores `.env`.

4. **Alternative: Set in Shell Environment directly:**
   * **PowerShell**:
     ```powershell
     $env:GNANI_API_KEY="your_actual_key_here"
     ```
   * **CMD (Windows)**:
     ```cmd
     set GNANI_API_KEY=your_actual_key_here
     ```
   * **Linux/macOS Bash**:
     ```bash
     export GNANI_API_KEY="your_actual_key_here"
     ```

5. **Voice Engine Modes:**
   * **Live Mode (`🟢 Live API`)**: Automatically active when `GNANI_API_KEY` is set. Makes live REST calls to `https://api.vachana.ai/stt/v3` and `https://api.vachana.ai/tts/v2` using model `timbre-v2.5` and voice `Kaveri`.
   * **Mock Mode (`🟠 Mock Engine`)**: Runs when `GNANI_API_KEY` is empty. Generates valid 16kHz PCM WAV bytes and uses deterministic test transcripts. All 31 unit tests and benchmarks pass in mock mode without consuming API credits.

6. **Verify Live Voice Connection:**
   Run the live integration test:
   ```bash
   pytest tests/test_voice.py -k test_real_gnani_network_integration -v
   ```

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
