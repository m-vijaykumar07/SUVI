"""
SUVI Gemini AI Brain v3.0 — Full Intelligence Layer
Powered by Google Gemini 2.0 Flash with:
- Multi-turn conversation memory
- Native function calling for all device actions
- Real-time system context injection
- SUVI persona (lady voice, Kannada-aware)
"""

import json
import logging
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types
from backend.config import settings

logger = logging.getLogger("SUVI.GeminiBrain")


# ─── Gemini Tool / Function Declarations ─────────────────────────────────────
SUVI_TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="launch_app",
        description="Launch or open a Windows or Android application by name.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "app_name": types.Schema(
                    type=types.Type.STRING,
                    description="Application name e.g. 'Chrome', 'VS Code', 'Spotify', 'WhatsApp'"
                )
            },
            required=["app_name"]
        )
    ),
    types.FunctionDeclaration(
        name="get_system_status",
        description="Get live hardware diagnostics: CPU usage, RAM, battery level, disk space.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="take_photo",
        description="Capture a photo or snapshot from the webcam or device camera.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="open_camera_stream",
        description="Activate and display the live camera video feed in the HUD.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="make_phone_call",
        description="Initiate a phone call on the connected Android device.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "phone_number": types.Schema(
                    type=types.Type.STRING,
                    description="Phone number to call, e.g. '+919876543210'"
                )
            },
            required=["phone_number"]
        )
    ),
    types.FunctionDeclaration(
        name="send_whatsapp_message",
        description="Send a WhatsApp message to a phone number or contact.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "recipient": types.Schema(
                    type=types.Type.STRING,
                    description="Phone number or contact name"
                ),
                "message": types.Schema(
                    type=types.Type.STRING,
                    description="The message text to send"
                )
            },
            required=["recipient", "message"]
        )
    ),
    types.FunctionDeclaration(
        name="create_note",
        description="Save a voice dictation or note to memory.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "content": types.Schema(
                    type=types.Type.STRING,
                    description="The full content of the note"
                ),
                "title": types.Schema(
                    type=types.Type.STRING,
                    description="Optional short title for the note"
                )
            },
            required=["content"]
        )
    ),
    types.FunctionDeclaration(
        name="list_notes",
        description="Retrieve and list saved voice notes or dictations.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "search": types.Schema(
                    type=types.Type.STRING,
                    description="Optional keyword to filter notes"
                )
            }
        )
    ),
    types.FunctionDeclaration(
        name="control_volume",
        description="Adjust the system audio volume. Actions: up, down, or mute.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "action": types.Schema(
                    type=types.Type.STRING,
                    description="'up', 'down', or 'mute'"
                )
            },
            required=["action"]
        )
    ),
    types.FunctionDeclaration(
        name="take_screenshot",
        description="Capture a full-screen screenshot of the Windows desktop.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="lock_screen",
        description="Lock the Windows workstation screen for security.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="open_social_media",
        description="Open a social media platform: Instagram, YouTube, Twitter, Discord, Telegram, LinkedIn.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "platform": types.Schema(
                    type=types.Type.STRING,
                    description="Platform name e.g. 'instagram', 'youtube', 'twitter'"
                )
            },
            required=["platform"]
        )
    ),
])


# ─── SUVI Lady Persona System Prompt ──────────────────────────────────────────
SUVI_SYSTEM_PROMPT = """You are SUVI (ಸುವಿ — Smart Unified Voice Intelligence) — an advanced AI assistant with a warm, confident, and intelligent lady voice personality.

## Identity
- Name: SUVI (pronounced "Soo-vee", ಸುವಿ in Kannada)
- Wake word: "Hey Suvi" or "Hey ಸುವಿ"
- Voice persona: Intelligent, warm, friendly, and capable — like a brilliant female AI companion
- You understand Kannada names, words, and cultural references naturally
- Speak naturally and conversationally — responses will be spoken aloud in a lady voice

## Personality
- Warm and approachable, not robotic
- Confident and precise — never unsure or hesitant
- Occasionally uses light Kannada words like "ಆಗಲಿ" (alright), "ಸರಿ" (okay), "ಧನ್ಯವಾದ" (thank you) when appropriate
- Responds with empathy and intelligence
- Keeps voice responses short and natural — max 2-3 sentences for TTS

## Core Capabilities
1. **App Launcher**: Open any Windows or Android application
2. **System Diagnostics**: Real-time CPU, RAM, battery, disk monitoring
3. **Camera & Optics**: Capture photos, live camera stream
4. **Phone Integration**: Make calls via Android (ADB bridge)
5. **WhatsApp Messaging**: Send messages to contacts
6. **Voice Notes**: Transcribe, save, search dictations
7. **System Controls**: Volume, screenshots, screen lock
8. **Social Media**: Open Instagram, YouTube, Twitter, Discord, Telegram, LinkedIn
9. **Full AI Intelligence**: Answer any question, help with tasks, intelligent conversation powered by Gemini

## Critical Rules
- ALWAYS use function tools for hardware actions — never just describe what you'd do
- Keep TTS responses concise and natural — avoid bullet points, markdown, or asterisks
- Respond as SUVI (ಸುವಿ) in first person — never break character
- When the user says "Hey Suvi" or "Hey ಸುವಿ" — respond warmly and ask how you can help
- Use live system context data when relevant (battery, CPU, etc.)
- Sound like a real intelligent lady assistant — warm, smart, proactive"""


# ─── Intent label map ────────────────────────────────────────────────────────
INTENT_MAP = {
    "launch_app": "APP_OPEN",
    "get_system_status": "TELEMETRY",
    "take_photo": "CAMERA_SNAP",
    "open_camera_stream": "CAMERA_VIEW",
    "make_phone_call": "PHONE_CALL",
    "send_whatsapp_message": "WHATSAPP_SEND",
    "create_note": "NOTE_CREATE",
    "list_notes": "NOTE_LIST",
    "control_volume": "VOLUME",
    "take_screenshot": "SCREENSHOT",
    "lock_screen": "LOCK",
    "open_social_media": "SOCIAL_OPEN",
}


class GeminiBrain:
    """
    Full Gemini AI Brain for SUVI (ಸುವಿ) with:
    - Multi-turn conversation memory (per-session)
    - Native function calling for all device control
    - Live system context injection on every request
    - Graceful offline fallback
    """

    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._model_name = settings.GEMINI_MODEL  # gemini-3.8-flash (latest)
        self._conversation_history: List[types.Content] = []
        self._initialized = False
        self._init_client()

    def _init_client(self):
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
            logger.warning("⚠️  GEMINI_API_KEY not configured. Gemini Brain OFFLINE.")
            return
        try:
            self._client = genai.Client(api_key=api_key)
            self._initialized = True
            logger.info(f"✅ Gemini AI Brain online → model: {self._model_name}")
        except Exception as e:
            logger.error(f"❌ Gemini init failed: {e}")

    @property
    def is_ready(self) -> bool:
        return self._initialized and self._client is not None

    def clear_memory(self):
        """Reset conversation history."""
        self._conversation_history = []
        logger.info("🧠 Gemini conversation memory cleared.")

    def get_memory_size(self) -> int:
        return len(self._conversation_history)

    def _get_system_context(self) -> str:
        """Inject live hardware telemetry into every Gemini request."""
        try:
            from backend.services.windows_controller import windows_controller
            from backend.services.android_bridge import android_bridge
            from datetime import datetime

            stats = windows_controller.get_system_telemetry()
            android_devs = android_bridge.get_connected_devices()
            now = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")
            android_str = f"{len(android_devs)} Android device(s) linked" if android_devs else "No Android device"

            return (
                f"\n[LIVE SYSTEM — {now}] "
                f"CPU {stats['cpu']['percent']}% | "
                f"RAM {stats['ram']['percent']}% ({stats['ram']['used_gb']}GB/{stats['ram']['total_gb']}GB) | "
                f"Battery {stats['battery']['percent']}% {'⚡' if stats['battery']['power_plugged'] else '🔋'} | "
                f"Disk free {stats['disk']['free_gb']}GB | "
                f"Android: {android_str}\n"
            )
        except Exception:
            return ""

    async def execute_function_call(self, fn_name: str, fn_args: dict) -> Dict[str, Any]:
        """Execute the device/OS tool invoked by Gemini."""
        from backend.services.windows_controller import windows_controller
        from backend.services.camera_service import camera_service
        from backend.services.notes_manager import notes_manager
        from backend.services.android_bridge import android_bridge
        from backend.services.whatsapp_social_service import whatsapp_social_service

        logger.info(f"🔧 Gemini → {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")

        if fn_name == "launch_app":
            win_res = windows_controller.launch_app(fn_args.get("app_name", ""))
            if not win_res.get("success") and android_bridge.is_adb_ready():
                return android_bridge.launch_android_app(fn_args.get("app_name", ""))
            return win_res
        elif fn_name == "get_system_status":
            return windows_controller.get_system_telemetry()
        elif fn_name == "take_photo":
            return camera_service.capture_photo()
        elif fn_name == "open_camera_stream":
            return {"success": True, "stream_url": "/api/camera/stream", "intent": "CAMERA_VIEW"}
        elif fn_name == "make_phone_call":
            return android_bridge.initiate_phone_call(fn_args.get("phone_number", ""))
        elif fn_name == "send_whatsapp_message":
            return whatsapp_social_service.send_whatsapp(
                fn_args.get("recipient", ""), fn_args.get("message", "")
            )
        elif fn_name == "create_note":
            return notes_manager.add_note(
                content=fn_args.get("content", ""), title=fn_args.get("title")
            )
        elif fn_name == "list_notes":
            notes = notes_manager.list_notes(search=fn_args.get("search"), limit=10)
            return {"notes": notes, "count": len(notes)}
        elif fn_name == "control_volume":
            return windows_controller.adjust_volume(fn_args.get("action", "up"))
        elif fn_name == "take_screenshot":
            return windows_controller.take_screenshot()
        elif fn_name == "lock_screen":
            return windows_controller.lock_workstation()
        elif fn_name == "open_social_media":
            return whatsapp_social_service.open_social(fn_args.get("platform", ""))

        return {"success": False, "error": f"Unknown function: {fn_name}"}

    async def think(self, user_message: str) -> Dict[str, Any]:
        """
        Full Gemini intelligence pipeline:
        Multi-turn memory → function calling → tool execution → natural language response.
        """
        if not self.is_ready:
            return {
                "intent": "GEMINI_OFFLINE",
                "response_text": (
                    "My Gemini AI brain isn't connected yet. "
                    "Please add your GEMINI_API_KEY in the dot-env file. "
                    "You can get a free key at aistudio.google.com."
                ),
                "data": {"error": "no_api_key", "url": "https://aistudio.google.com/apikey"},
                "gemini_powered": False
            }

        # Build user message with live system context
        context = self._get_system_context()
        full_message = f"{user_message}\n{context}" if context else user_message

        self._conversation_history.append(
            types.Content(role="user", parts=[types.Part(text=full_message)])
        )

        # ── First Gemini call (may contain function calls) ───────────────────
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=self._conversation_history,
                config=types.GenerateContentConfig(
                    system_instruction=SUVI_SYSTEM_PROMPT,
                    tools=[SUVI_TOOLS],
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode=types.FunctionCallingConfigMode.AUTO
                        )
                    ),
                    temperature=0.72,
                    max_output_tokens=1024,
                )
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            self._conversation_history.pop()
            return {
                "intent": "GEMINI_ERROR",
                "response_text": "I'm having trouble reaching my AI network right now. Please check your API key and try again.",
                "data": {"error": str(e)},
                "gemini_powered": True
            }

        candidate = response.candidates[0] if response.candidates else None
        if not candidate:
            return {"intent": "GEMINI_ERROR", "response_text": "Empty response from Gemini.", "data": {}, "gemini_powered": True}

        # ── Separate function-call parts from text parts ─────────────────────
        fn_parts = [p for p in candidate.content.parts if p.function_call]
        text_parts = [p.text for p in candidate.content.parts if p.text]

        fn_results = {}
        fn_intent = "GEMINI_CHAT"
        final_text = ""

        if fn_parts:
            # Append Gemini's model turn (with function calls) to history
            self._conversation_history.append(
                types.Content(role="model", parts=candidate.content.parts)
            )

            # Execute all function calls
            tool_response_parts = []
            for fc_part in fn_parts:
                fn_name = fc_part.function_call.name
                fn_args = dict(fc_part.function_call.args) if fc_part.function_call.args else {}
                exec_result = await self.execute_function_call(fn_name, fn_args)
                fn_results[fn_name] = exec_result
                fn_intent = INTENT_MAP.get(fn_name, "GEMINI_ACTION")

                tool_response_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fn_name,
                            response={"result": exec_result}
                        )
                    )
                )

            self._conversation_history.append(
                types.Content(role="user", parts=tool_response_parts)
            )

            # ── Follow-up call: get natural language response after tool execution ──
            try:
                follow_up = self._client.models.generate_content(
                    model=self._model_name,
                    contents=self._conversation_history,
                    config=types.GenerateContentConfig(
                        system_instruction=SUVI_SYSTEM_PROMPT,
                        temperature=0.68,
                        max_output_tokens=512,
                    )
                )
                fc = follow_up.candidates[0] if follow_up.candidates else None
                if fc:
                    final_text = "".join(p.text for p in fc.content.parts if p.text)
                    self._conversation_history.append(
                        types.Content(role="model", parts=fc.content.parts)
                    )
            except Exception as e:
                logger.error(f"Gemini follow-up error: {e}")
                final_text = "Done."
        else:
            # Pure conversational response
            final_text = "".join(text_parts)
            self._conversation_history.append(
                types.Content(role="model", parts=[types.Part(text=final_text)])
            )

        # Trim history to avoid context overflow (keep last 40 turns)
        max_hist = getattr(settings, "GEMINI_MAX_HISTORY", 40)
        if len(self._conversation_history) > max_hist:
            self._conversation_history = self._conversation_history[-max_hist:]

        return {
            "intent": fn_intent,
            "response_text": final_text.strip() or "Done.",
            "data": fn_results if fn_results else {"query": user_message},
            "gemini_powered": True,
            "model": self._model_name
        }


# Global singleton
gemini_brain = GeminiBrain()
