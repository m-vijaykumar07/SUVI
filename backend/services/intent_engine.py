import re
import time
from typing import Dict, Any, Optional
from datetime import datetime
from backend.services.windows_controller import windows_controller
from backend.services.camera_service import camera_service
from backend.services.notes_manager import notes_manager
from backend.services.android_bridge import android_bridge
from backend.services.whatsapp_social_service import whatsapp_social_service
from backend.security import verify_action_pin

class IntentEngine:
    """Smart Unified Voice Intelligence (SUVI) natural language intent resolver and execution dispatcher."""

    def __init__(self):
        pass

    async def process_command(self, query: str, pin: Optional[str] = None) -> Dict[str, Any]:
        """Parse spoken or typed user command and execute matching intent action."""
        if not query or not query.strip():
            return {
                "intent": "EMPTY",
                "response_text": "I am listening. How can I assist you?",
                "data": None
            }

        text = query.strip()
        lower = text.lower()

        # 1. Greetings / Assistant Identity
        if any(w in lower for w in ["who are you", "what is your name", "what are you"]):
            return {
                "intent": "IDENTITY",
                "response_text": "I am SUVI — Smart Unified Voice Intelligence. I operate your Windows workstation, Android phone, cameras, dictations, and communications.",
                "data": {"name": "SUVI", "version": "2.0.0"}
            }

        if re.search(r"^(hello|hi|hey|wake up|good (morning|afternoon|evening)|greetings)(\s+suvi)?", lower):
            return {
                "intent": "GREETING",
                "response_text": f"Greetings! Systems online and ready for your command.",
                "data": {"timestamp": time.time()}
            }

        # 2. Time & Date
        if "what time" in lower or "current time" in lower or "clock" in lower:
            now_str = datetime.now().strftime("%I:%M %p")
            return {
                "intent": "TIME",
                "response_text": f"The current time is {now_str}.",
                "data": {"time": now_str}
            }

        if "date" in lower or "day is it" in lower:
            today_str = datetime.now().strftime("%A, %B %d, %Y")
            return {
                "intent": "DATE",
                "response_text": f"Today is {today_str}.",
                "data": {"date": today_str}
            }

        # 3. System Telemetry / Hardware Status
        if any(k in lower for k in ["system status", "battery", "cpu", "ram", "telemetry", "diagnostics", "hardware status"]):
            stats = windows_controller.get_system_telemetry()
            batt = stats["battery"]["percent"]
            cpu = stats["cpu"]["percent"]
            ram = stats["ram"]["percent"]
            response = f"System diagnostics: CPU is at {cpu}%, RAM utilization is at {ram}%, and battery is at {batt}%."
            return {
                "intent": "TELEMETRY",
                "response_text": response,
                "data": stats
            }

        # 4. Camera & Photography
        if any(k in lower for k in ["take a photo", "take photo", "take picture", "capture photo", "snap picture"]):
            snap_res = camera_service.capture_photo()
            if snap_res["success"]:
                return {
                    "intent": "CAMERA_SNAP",
                    "response_text": "Photo captured and cataloged in security archives.",
                    "data": snap_res
                }
            else:
                return {
                    "intent": "CAMERA_SNAP",
                    "response_text": f"Camera notice: {snap_res.get('error', 'Device busy.')}",
                    "data": snap_res
                }

        if any(k in lower for k in ["open camera", "show camera", "activate camera", "turn on camera"]):
            return {
                "intent": "CAMERA_VIEW",
                "response_text": "Activating optical recon stream.",
                "data": {"stream_url": "/api/camera/stream"}
            }

        # 5. Phone Call Intent (Android Bridge)
        call_match = re.search(r"(?:call|phone|dial|make a call to)\s+([\+\d\s\-\(\)\w]+)", lower)
        if call_match:
            target = call_match.group(1).strip()
            # If target has digits or name
            call_res = android_bridge.initiate_phone_call(target)
            return {
                "intent": "PHONE_CALL",
                "response_text": f"Initiating call to {target}.",
                "data": call_res
            }

        # 6. WhatsApp Message Intent
        # Patterns like: "send whatsapp to <target> saying <message>" or "text <target> on whatsapp <message>"
        wa_match = re.search(r"(?:send\s+whatsapp\s+to|whatsapp|text)\s+([\+\d\w\s]+?)\s+(?:saying|message|that)\s+(.+)", lower)
        if wa_match:
            recipient = wa_match.group(1).strip()
            msg_content = wa_match.group(2).strip()
            wa_res = whatsapp_social_service.send_whatsapp(recipient, msg_content)
            return {
                "intent": "WHATSAPP_SEND",
                "response_text": f"Dispatching WhatsApp message to {recipient}.",
                "data": wa_res
            }

        # Direct WhatsApp Open
        if "open whatsapp" in lower or "launch whatsapp" in lower:
            windows_controller.launch_app("whatsapp")
            return {
                "intent": "APP_OPEN",
                "response_text": "Opening WhatsApp.",
                "data": {"app": "whatsapp"}
            }

        # 7. Voice Notes & Dictation
        # e.g., "write note buy milk" or "take note meeting tomorrow" or "note down review code"
        note_match = re.search(r"(?:write\s+note|take\s+note|note\s+down|remember\s+that|add\s+note)\s+(.+)", lower)
        if note_match:
            note_text = note_match.group(1).strip()
            res = notes_manager.add_note(content=note_text)
            return {
                "intent": "NOTE_CREATE",
                "response_text": f"Note recorded: {note_text}",
                "data": res
            }

        if any(k in lower for k in ["show notes", "show my notes", "read my notes", "list notes", "my notes"]):
            notes = notes_manager.list_notes(limit=5)
            if not notes:
                return {
                    "intent": "NOTE_LIST",
                    "response_text": "You have no recorded notes in memory.",
                    "data": {"notes": []}
                }
            count = len(notes)
            sample_titles = ", ".join(f"'{n['title']}'" for n in notes[:3])
            return {
                "intent": "NOTE_LIST",
                "response_text": f"Retrieved {count} notes. Recent entries include: {sample_titles}.",
                "data": {"notes": notes}
            }

        # 8. Volume Control
        if "volume up" in lower or "increase volume" in lower or "louder" in lower:
            vol_res = windows_controller.adjust_volume("up")
            return {
                "intent": "VOLUME",
                "response_text": "Increasing volume.",
                "data": vol_res
            }
        if "volume down" in lower or "decrease volume" in lower or "quieter" in lower:
            vol_res = windows_controller.adjust_volume("down")
            return {
                "intent": "VOLUME",
                "response_text": "Decreasing volume.",
                "data": vol_res
            }
        if "mute" in lower or "unmute" in lower:
            vol_res = windows_controller.adjust_volume("mute")
            return {
                "intent": "VOLUME",
                "response_text": "Toggling mute.",
                "data": vol_res
            }

        # 9. Screenshot
        if any(k in lower for k in ["take screenshot", "screenshot", "capture screen"]):
            sc_res = windows_controller.take_screenshot()
            if sc_res["success"]:
                return {
                    "intent": "SCREENSHOT",
                    "response_text": "Screenshot captured and stored.",
                    "data": sc_res
                }
            return {
                "intent": "SCREENSHOT",
                "response_text": "Failed to capture screenshot.",
                "data": sc_res
            }

        # 10. Security Lock Screen
        if any(k in lower for k in ["lock screen", "lock workstation", "lock pc", "lock computer"]):
            lock_res = windows_controller.lock_workstation()
            return {
                "intent": "LOCK",
                "response_text": "Workstation locked for security.",
                "data": lock_res
            }

        # 11. Social Media Launchers
        for platform in ["instagram", "twitter", "telegram", "youtube", "discord", "linkedin", "reddit"]:
            if f"open {platform}" in lower or f"launch {platform}" in lower:
                res = whatsapp_social_service.open_social(platform)
                return {
                    "intent": "SOCIAL_OPEN",
                    "response_text": f"Opening {platform.capitalize()}.",
                    "data": res
                }

        # 12. Application Launch (Windows or Android)
        open_match = re.search(r"^(?:open|launch|start|run)\s+(.+)", lower)
        if open_match:
            app_target = open_match.group(1).strip()
            # Clean common words like "the", "app", "application"
            app_target = re.sub(r"^(the|app|application)\s+", "", app_target)
            
            # Check Windows first
            win_res = windows_controller.launch_app(app_target)
            if win_res["success"]:
                return {
                    "intent": "APP_OPEN",
                    "response_text": f"Launching {app_target}.",
                    "data": win_res
                }
            # Try Android if connected
            if android_bridge.is_adb_ready() and android_bridge.get_connected_devices():
                and_res = android_bridge.launch_android_app(app_target)
                if and_res["success"]:
                    return {
                        "intent": "APP_OPEN",
                        "response_text": f"Launching {app_target} on Android device.",
                        "data": and_res
                    }

            return {
                "intent": "APP_OPEN",
                "response_text": f"Attempted to launch {app_target}. Please confirm the app name.",
                "data": win_res
            }

        # 13. Conversational Intelligence Fallback
        # Smart conversational responses with persona
        return self._generate_conversational_response(text)

    def _generate_conversational_response(self, text: str) -> Dict[str, Any]:
        """Generate conversational voice intelligence response."""
        lower = text.lower()
        if "how are you" in lower:
            resp = "All core systems are operational at peak efficiency. Ready for your instructions."
        elif "thank" in lower:
            resp = "Always a pleasure to serve. Standing by."
        elif "what can you do" in lower or "help" in lower:
            resp = "I can launch any Windows or Android app, initiate phone calls, send WhatsApp messages, control cameras, take notes, capture screenshots, and monitor hardware."
        else:
            resp = f"Processed request: '{text}'. If this is a system command, you can say open an app, take a note, or check system status."

        return {
            "intent": "CONVERSATION",
            "response_text": resp,
            "data": {"query": text}
        }

intent_engine = IntentEngine()
