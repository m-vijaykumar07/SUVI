"""
SUVI Intent Engine v3.0 — Hybrid Local-Fast-Path & Gemini AI Brain
Architecture:
1. Fast-path local dispatch for hardware/system commands (sub-10ms, offline capable)
2. Wake word detection: "Hey Suvi (ಸುವಿ)" with Kannada phonetic awareness
3. Unmatched/conversational queries route to Gemini AI Brain with multi-turn memory
"""

import re
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from backend.services.windows_controller import windows_controller
from backend.services.camera_service import camera_service
from backend.services.notes_manager import notes_manager
from backend.services.android_bridge import android_bridge
from backend.services.whatsapp_social_service import whatsapp_social_service
from backend.services.gemini_brain import gemini_brain
from backend.config import settings

logger = logging.getLogger("SUVI.IntentEngine")

# ─── Wake word variants including Kannada phonetics ────────────────────────────
_WAKE_PATTERNS = [
    r"^hey\s+su[vb]i{1,2}",
    r"^hey\s+sou?vi",
    r"^hey\s+soo?[vb]i",
    r"^hey\s+ಸುವಿ",
    r"^(?:wake up|start|activate)\s+su[vb]i",
]
_WAKE_REGEX = re.compile("|".join(_WAKE_PATTERNS), re.IGNORECASE | re.UNICODE)


def _is_wake_word(text: str) -> bool:
    """Check if spoken/typed text is a wake-word trigger for SUVI (ಸುವಿ)."""
    lower = text.strip().lower()
    if lower in ("suvi", "hey suvi", "hey ಸುವಿ"):
        return True
    aliases = [a.strip() for a in settings.WAKE_WORD_ALIASES.split(",")]
    if lower in aliases:
        return True
    return bool(_WAKE_REGEX.match(lower))


class IntentEngine:
    """Smart Unified Voice Intelligence (SUVI) v3.0 Intent Engine."""

    def __init__(self):
        pass

    async def process_command(self, query: str, pin: Optional[str] = None) -> Dict[str, Any]:
        """Parse user query: try instant local fast-path first, fall back to Gemini AI Brain."""
        if not query or not query.strip():
            return {
                "intent": "EMPTY",
                "response_text": "I am listening. How can I help you?",
                "data": None,
                "gemini_powered": False
            }

        text = query.strip()
        lower = text.lower()

        # 1. Wake word — "Hey Suvi" / "Hey ಸುವಿ"
        if _is_wake_word(text):
            hour = datetime.now().hour
            greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
            ready = gemini_brain.is_ready
            return {
                "intent": "WAKE_WORD",
                "response_text": f"{greeting}! I am Suvi, your AI assistant. Gemini AI brain is {'online and ready' if ready else 'offline'}. How can I help you?",
                "data": {"timestamp": time.time(), "gemini_ready": ready, "wake_word": "hey suvi (ಸುವಿ)"},
                "gemini_powered": False
            }

        # 2. Identity / Assistant info
        if any(w in lower for w in ["who are you", "what is your name", "what are you"]):
            return {
                "intent": "IDENTITY",
                "response_text": "I am SUVI (ಸುವಿ) — Smart Unified Voice Intelligence, powered by Google Gemini. I operate your Windows workstation, Android phone, cameras, notes, and communications with a warm lady voice.",
                "data": {"name": "SUVI", "version": settings.APP_VERSION, "voice": settings.DEFAULT_TTS_VOICE},
                "gemini_powered": False
            }

        # 3. AI / Memory Control
        if any(k in lower for k in ["clear memory", "forget everything", "reset conversation", "new session", "start fresh"]):
            gemini_brain.clear_memory()
            return {
                "intent": "MEMORY_CLEAR",
                "response_text": "Conversation memory cleared. Starting fresh.",
                "data": {"cleared": True},
                "gemini_powered": False
            }

        if any(k in lower for k in ["gemini status", "ai status", "brain status", "is ai on"]):
            ready = gemini_brain.is_ready
            hist = gemini_brain.get_memory_size()
            return {
                "intent": "AI_STATUS",
                "response_text": f"Gemini AI Brain is {'online and ready' if ready else 'offline'}. Active model: {settings.GEMINI_MODEL} with {hist} memory turns.",
                "data": {"ready": ready, "model": settings.GEMINI_MODEL, "history_turns": hist},
                "gemini_powered": ready
            }

        # 4. Standard Greetings
        if re.search(r"^(hello|hi|hey|good (morning|afternoon|evening)|greetings)(\s+suvi)?", lower):
            return {
                "intent": "GREETING",
                "response_text": "Hello! All systems online. What would you like me to do?",
                "data": {"timestamp": time.time()},
                "gemini_powered": False
            }

        # 5. Time & Date
        if "what time" in lower or "current time" in lower or lower == "time":
            now_str = datetime.now().strftime("%I:%M %p")
            return {
                "intent": "TIME",
                "response_text": f"The current time is {now_str}.",
                "data": {"time": now_str},
                "gemini_powered": False
            }

        if "what date" in lower or "current date" in lower or "day is it" in lower or lower == "date":
            today_str = datetime.now().strftime("%A, %B %d, %Y")
            return {
                "intent": "DATE",
                "response_text": f"Today is {today_str}.",
                "data": {"date": today_str},
                "gemini_powered": False
            }

        # 6. System Telemetry / Hardware Status
        if any(k in lower for k in ["system status", "battery", "cpu", "ram", "telemetry", "diagnostics", "hardware status"]):
            stats = windows_controller.get_system_telemetry()
            batt = stats["battery"]["percent"]
            cpu = stats["cpu"]["percent"]
            ram = stats["ram"]["percent"]
            response = f"System diagnostics: CPU is at {cpu}%, RAM utilization is at {ram}%, and battery is at {batt}%."
            return {
                "intent": "TELEMETRY",
                "response_text": response,
                "data": stats,
                "gemini_powered": False
            }

        # 7. Camera & Photography
        if any(k in lower for k in ["take a photo", "take photo", "take picture", "capture photo", "snap picture"]):
            snap_res = camera_service.capture_photo()
            return {
                "intent": "CAMERA_SNAP",
                "response_text": "Photo captured and stored." if snap_res.get("success") else f"Camera notice: {snap_res.get('error', 'Device busy.')}",
                "data": snap_res,
                "gemini_powered": False
            }

        if any(k in lower for k in ["open camera", "show camera", "activate camera", "turn on camera"]):
            return {
                "intent": "CAMERA_VIEW",
                "response_text": "Activating camera feed.",
                "data": {"stream_url": "/api/camera/stream"},
                "gemini_powered": False
            }

        # 8. Phone Call Intent (Android Bridge)
        call_match = re.search(r"(?:call|phone|dial|make a call to)\s+([\+\d\s\-\(\)\w]+)", lower)
        if call_match:
            target = call_match.group(1).strip()
            call_res = android_bridge.initiate_phone_call(target)
            return {
                "intent": "PHONE_CALL",
                "response_text": f"Initiating call to {target}.",
                "data": call_res,
                "gemini_powered": False
            }

        # 9. WhatsApp Message Intent
        wa_match = re.search(r"(?:send\s+whatsapp\s+to|whatsapp|text)\s+([\+\d\w\s]+?)\s+(?:saying|message|that)\s+(.+)", lower)
        if wa_match:
            recipient = wa_match.group(1).strip()
            msg_content = wa_match.group(2).strip()
            wa_res = whatsapp_social_service.send_whatsapp(recipient, msg_content)
            return {
                "intent": "WHATSAPP_SEND",
                "response_text": f"Dispatching WhatsApp message to {recipient}.",
                "data": wa_res,
                "gemini_powered": False
            }

        if "open whatsapp" in lower or "launch whatsapp" in lower:
            windows_controller.launch_app("whatsapp")
            return {
                "intent": "APP_OPEN",
                "response_text": "Opening WhatsApp.",
                "data": {"app": "whatsapp"},
                "gemini_powered": False
            }

        # 10. Voice Notes & Dictation
        note_match = re.search(r"(?:write\s+note|take\s+note|note\s+down|remember\s+that|add\s+note)\s+(.+)", lower)
        if note_match:
            note_text = note_match.group(1).strip()
            res = notes_manager.add_note(content=note_text)
            return {
                "intent": "NOTE_CREATE",
                "response_text": f"Note recorded: {note_text}",
                "data": res,
                "gemini_powered": False
            }

        if any(k in lower for k in ["show notes", "show my notes", "read my notes", "list notes", "my notes"]):
            notes = notes_manager.list_notes(limit=5)
            if not notes:
                return {
                    "intent": "NOTE_LIST",
                    "response_text": "You have no recorded notes in memory.",
                    "data": {"notes": []},
                    "gemini_powered": False
                }
            count = len(notes)
            sample_titles = ", ".join(f"'{n['title']}'" for n in notes[:3])
            return {
                "intent": "NOTE_LIST",
                "response_text": f"Retrieved {count} notes. Recent entries include: {sample_titles}.",
                "data": {"notes": notes},
                "gemini_powered": False
            }

        # 11. Volume Control
        if "volume up" in lower or "increase volume" in lower or "louder" in lower:
            vol_res = windows_controller.adjust_volume("up")
            return {
                "intent": "VOLUME",
                "response_text": "Increasing volume.",
                "data": vol_res,
                "gemini_powered": False
            }
        if "volume down" in lower or "decrease volume" in lower or "quieter" in lower:
            vol_res = windows_controller.adjust_volume("down")
            return {
                "intent": "VOLUME",
                "response_text": "Decreasing volume.",
                "data": vol_res,
                "gemini_powered": False
            }
        if "mute" in lower or "unmute" in lower:
            vol_res = windows_controller.adjust_volume("mute")
            return {
                "intent": "VOLUME",
                "response_text": "Toggling mute.",
                "data": vol_res,
                "gemini_powered": False
            }

        # 12. Screenshot
        if any(k in lower for k in ["take screenshot", "screenshot", "capture screen"]):
            sc_res = windows_controller.take_screenshot()
            return {
                "intent": "SCREENSHOT",
                "response_text": "Screenshot captured and stored." if sc_res.get("success") else "Failed to capture screenshot.",
                "data": sc_res,
                "gemini_powered": False
            }

        # 13. Screen Lock
        if any(k in lower for k in ["lock screen", "lock workstation", "lock pc", "lock computer"]):
            lock_res = windows_controller.lock_workstation()
            return {
                "intent": "LOCK",
                "response_text": "Workstation locked for security.",
                "data": lock_res,
                "gemini_powered": False
            }

        # 14. Social Media
        for platform in ["instagram", "twitter", "telegram", "youtube", "discord", "linkedin", "reddit"]:
            if f"open {platform}" in lower or f"launch {platform}" in lower:
                res = whatsapp_social_service.open_social(platform)
                return {
                    "intent": "SOCIAL_OPEN",
                    "response_text": f"Opening {platform.capitalize()}.",
                    "data": res,
                    "gemini_powered": False
                }

        # 15. Explicit App Open
        open_match = re.search(r"^(?:open|launch|start|run)\s+(.+)", lower)
        if open_match:
            app_target = open_match.group(1).strip()
            app_target = re.sub(r"^(the|app|application)\s+", "", app_target)
            win_res = windows_controller.launch_app(app_target)
            if win_res.get("success"):
                return {
                    "intent": "APP_OPEN",
                    "response_text": f"Launching {app_target}.",
                    "data": win_res,
                    "gemini_powered": False
                }
            if android_bridge.is_adb_ready() and android_bridge.get_connected_devices():
                and_res = android_bridge.launch_android_app(app_target)
                if and_res.get("success"):
                    return {
                        "intent": "APP_OPEN",
                        "response_text": f"Launching {app_target} on Android device.",
                        "data": and_res,
                        "gemini_powered": False
                    }
            return {
                "intent": "APP_OPEN",
                "response_text": f"Attempted to launch {app_target}.",
                "data": win_res,
                "gemini_powered": False
            }

        # ── 16. Fallback to Gemini AI Brain ──────────────────────────────────
        if gemini_brain.is_ready:
            return await gemini_brain.think(text)

        return {
            "intent": "CONVERSATION",
            "response_text": f"I heard: '{text}'. You can ask me to open apps, check battery/CPU, take photos, or configure GEMINI_API_KEY for full conversational intelligence.",
            "data": {"query": text},
            "gemini_powered": False
        }


intent_engine = IntentEngine()
