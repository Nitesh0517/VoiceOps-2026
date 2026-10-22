"""Global application configuration for VoiceOps 2026."""
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load local environment variables from .env if available
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Locate dataset directory
DATASET_DIR = BASE_DIR / "Capstone_Project_Dataset_FTTT_2026"
if not DATASET_DIR.exists():
    DATASET_DIR = BASE_DIR


class Settings(BaseModel):
    APP_NAME: str = "VoiceOps-2026"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    BASE_DIR: Path = BASE_DIR
    
    # Dataset Reference Date frozen on 20 October 2026 as per KB-00.2
    REFERENCE_DATE: str = "2026-10-20"
    
    # Database
    DATABASE_PATH: Path = BASE_DIR / "data" / "zentromart.db"
    DATA_CSV_DIR: Path = DATASET_DIR / "data"
    KB_DIR: Path = DATASET_DIR / "kb"
    PRACTICE_DIR: Path = DATASET_DIR / "practice"
    
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
