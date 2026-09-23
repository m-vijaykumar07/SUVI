import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "SUVI - Smart Unified Voice Intelligence"
    APP_VERSION: str = "2.0.0"
    BASE_DIR: Path = BASE_DIR
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "suvi-jarvis-super-secret-key-change-in-production-2026"
    MASTER_PIN: str = "1234"  # Master voice / action PIN for sensitive actions
    API_TOKEN: str = "suvi-core-token-secure-v2"

    # Storage paths
    DATA_DIR: Path = BASE_DIR / "data"
    CAPTURES_DIR: Path = BASE_DIR / "data" / "captures"
    AUDIO_DIR: Path = BASE_DIR / "data" / "audio"
    DB_PATH: Path = BASE_DIR / "data" / "suvi.db"

    # Voice Engine Settings
    DEFAULT_TTS_VOICE: str = "en-US-ChristopherNeural"  # Realistic futuristic male AI voice
    FALLBACK_TTS_VOICE: str = "en-US-GuyNeural"
    TTS_RATE: str = "+0%"
    TTS_PITCH: str = "+0Hz"

    # Android ADB Settings
    ADB_PATH: str = "adb"
    ANDROID_DEVICE_IP: str = ""  # e.g. "192.168.1.100:5555" for wireless ADB

    # Optional AI LLM Provider (for open conversation)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
