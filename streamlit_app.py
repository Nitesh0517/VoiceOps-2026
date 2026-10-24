"""VoiceOps 2026 — Root Streamlit Entrypoint.

Allows running either:
    streamlit run frontend/app.py
or
    streamlit run streamlit_app.py
"""
import sys
from pathlib import Path
import runpy

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_FRONTEND_APP = _ROOT / "frontend" / "app.py"
runpy.run_path(str(_FRONTEND_APP), run_name="__main__")
