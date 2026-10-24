"""Global application configuration for VoiceOps 2026."""
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment variables from .env if available across workspace paths
for env_path in [BASE_DIR / ".env", BASE_DIR.parent / ".env", Path.cwd() / ".env"]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
load_dotenv()


# Locate dataset directory with resilient multi-path discovery
DATASET_DIR = BASE_DIR
for candidate in [
    BASE_DIR / "Capstone_Project_Dataset_FTTT_2026",
    BASE_DIR.parent / "Capstone_Project_Dataset_FTTT_2026",
    BASE_DIR,
    BASE_DIR.parent
]:
    if (candidate / "data" / "pincodes.csv").exists():
        DATASET_DIR = candidate
        break

# Resolve data, kb, and practice dirs
DATA_CSV_DIR = DATASET_DIR / "data" if (DATASET_DIR / "data").exists() else BASE_DIR / "data"
KB_DIR = DATASET_DIR / "kb" if (DATASET_DIR / "kb").exists() else (BASE_DIR / "kb" if (BASE_DIR / "kb").exists() else BASE_DIR.parent / "kb")
PRACTICE_DIR = DATASET_DIR / "practice" if (DATASET_DIR / "practice").exists() else (BASE_DIR / "practice" if (BASE_DIR / "practice").exists() else BASE_DIR.parent / "practice")


class Settings(BaseModel):
    APP_NAME: str = "VoiceOps-2026"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    BASE_DIR: Path = BASE_DIR
    
    # Dataset Reference Date frozen on 20 October 2026 as per KB-00.2
    REFERENCE_DATE: str = "2026-10-20"
    
    # Database
    DATABASE_PATH: Path = BASE_DIR / "data" / "zentromart.db"
    DATA_CSV_DIR: Path = DATA_CSV_DIR
    KB_DIR: Path = KB_DIR
    PRACTICE_DIR: Path = PRACTICE_DIR
    
    # API Keys
    GNANI_API_KEY: str = Field(default_factory=lambda: os.getenv("GNANI_API_KEY", ""))
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    OPENAI_API_KEY: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    
    # Voice Config
    GNANI_BASE_URL: str = "https://api.vachana.ai"
    DEFAULT_VOICE: str = "Kaveri"
    DEFAULT_TTS_MODEL: str = "timbre-v2.5"
    DEFAULT_LANGUAGE_CODE: str = "en-IN"
    
    # Host & Port
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000


settings = Settings()
