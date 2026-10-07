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

    # Voice Engine Settings  (Lady voice — warm & intelligent)
    # Female neural voices: en-US-JennyNeural | en-US-AriaNeural | en-IN-NeerjaNeural | en-GB-SoniaNeural
    DEFAULT_TTS_VOICE: str = "en-US-JennyNeural"   # Primary: warm US lady voice
    FALLBACK_TTS_VOICE: str = "en-IN-NeerjaNeural"  # Fallback: Indian lady voice
    TTS_RATE: str = "+5%"      # Slightly faster — natural conversation pace
    TTS_PITCH: str = "+3Hz"    # Slightly higher pitch for lady voice character

    # Wake Word  (Kannada: ಸುವಿ pronounced "Soo-vee")
    WAKE_WORD: str = "hey suvi"
    WAKE_WORD_KANNADA: str = "hey ಸುವಿ"
    WAKE_WORD_ALIASES: str = "suvi,hey suvii,hey souvi,hey soobi,hey suby"  # phonetic variants

    # Android ADB Settings
    ADB_PATH: str = "adb"
    ANDROID_DEVICE_IP: str = ""  # e.g. "192.168.1.100:5555" for wireless ADB

    # ── Gemini AI Brain Settings ──────────────────────────────────────────────
    # Get your free API key at: https://aistudio.google.com/apikey
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"  # Latest fast model for real-time voice
    GEMINI_MAX_HISTORY: int = 40            # Max conversation turns kept in memory
    OPENAI_API_KEY: str = ""               # Optional OpenAI fallback

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
