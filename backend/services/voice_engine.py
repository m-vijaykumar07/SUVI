import os
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import edge_tts
from backend.config import settings

class VoiceEngine:
    """Provides high-definition Neural Text-To-Speech (edge-tts) and offline fallback (pyttsx3)."""

    def __init__(self):
        self.default_voice = settings.DEFAULT_TTS_VOICE
        self._offline_engine = None

    def _get_offline_engine(self):
        """Lazy load pyttsx3 offline engine if needed."""
        if self._offline_engine is None:
            try:
                import pyttsx3
                self._offline_engine = pyttsx3.init()
                self._offline_engine.setProperty('rate', 180)
            except Exception:
                self._offline_engine = False
        return self._offline_engine

    async def speak_text_async(self, text: str, voice: Optional[str] = None) -> Dict[str, Any]:
        """Convert text to speech audio using edge-tts neural synthesis."""
        if not text or not text.strip():
            return {"success": False, "error": "Empty text provided."}

        clean_text = text.strip()
        voice_name = voice or self.default_voice

        # Cache key based on voice and text
        hash_digest = hashlib.md5(f"{voice_name}_{clean_text}".encode("utf-8")).hexdigest()
        filename = f"tts_{hash_digest}.mp3"
        filepath = settings.AUDIO_DIR / filename
        audio_url = f"/api/audio/{filename}"

        # If already generated and cached, reuse immediately
        if filepath.exists() and filepath.stat().st_size > 0:
            return {
                "success": True,
                "audio_url": audio_url,
                "cached": True,
                "text": clean_text,
                "voice": voice_name
            }

        # Try Edge Neural TTS first (highest quality)
        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=voice_name,
                rate=settings.TTS_RATE,
                pitch=settings.TTS_PITCH
            )
            await communicate.save(str(filepath))
            return {
                "success": True,
                "audio_url": audio_url,
                "cached": False,
                "text": clean_text,
                "voice": voice_name
            }
        except Exception as e:
            # Fallback to pyttsx3 offline synthesis
            return self._speak_offline_fallback(clean_text, filepath, audio_url)

    def _speak_offline_fallback(self, text: str, filepath: Path, audio_url: str) -> Dict[str, Any]:
        """Generate offline speech using pyttsx3."""
        engine = self._get_offline_engine()
        if not engine:
            return {"success": False, "error": "Voice synthesis failed and offline engine unavailable."}

        try:
            # pyttsx3 works best with .wav
            wav_path = filepath.with_suffix(".wav")
            engine.save_to_file(text, str(wav_path))
            engine.runAndWait()

            wav_url = f"/api/audio/{wav_path.name}"
            return {
                "success": True,
                "audio_url": wav_url,
                "cached": False,
                "fallback": True,
                "text": text
            }
        except Exception as err:
            return {"success": False, "error": f"TTS synthesis error: {str(err)}"}

    @staticmethod
    def get_available_voices() -> List[Dict[str, str]]:
        """List recommended modern AI voices."""
        return [
            {"id": "en-US-ChristopherNeural", "name": "Christopher (JARVIS / British-American Male)", "gender": "Male"},
            {"id": "en-US-GuyNeural", "name": "Guy (Modern American Male)", "gender": "Male"},
            {"id": "en-US-AriaNeural", "name": "Aria (Crisp Futuristic Female)", "gender": "Female"},
            {"id": "en-GB-RyanNeural", "name": "Ryan (Classic British JARVIS)", "gender": "Male"},
            {"id": "en-IN-PrabhatNeural", "name": "Prabhat (Indian English Male)", "gender": "Male"},
            {"id": "en-IN-NeerjaNeural", "name": "Neerja (Indian English Female)", "gender": "Female"},
        ]

voice_engine = VoiceEngine()
