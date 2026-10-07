import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings
from backend.security import verify_api_key, require_pin_auth, verify_action_pin
from backend.services.windows_controller import windows_controller
from backend.services.camera_service import camera_service
from backend.services.notes_manager import notes_manager
from backend.services.android_bridge import android_bridge
from backend.services.whatsapp_social_service import whatsapp_social_service
from backend.services.voice_engine import voice_engine
from backend.services.intent_engine import intent_engine
from backend.services.gemini_brain import gemini_brain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SUVI")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Smart Unified Voice Intelligence - Cross-Platform Assistant"
)

# Enable CORS for local cross-device access (Windows & Android on Wi-Fi)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset directories
frontend_dir = settings.BASE_DIR / "frontend"
app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")
app.mount("/api/captures", StaticFiles(directory=str(settings.CAPTURES_DIR)), name="captures")
app.mount("/api/audio", StaticFiles(directory=str(settings.AUDIO_DIR)), name="audio")

# ----------------- Request Models ----------------- #

class CommandRequest(BaseModel):
    command: str
    pin: Optional[str] = None
    voice_enabled: bool = True

class SpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = None

class NoteCreateRequest(BaseModel):
    title: Optional[str] = None
    content: str
    category: Optional[str] = "voice_dictation"

class CallRequest(BaseModel):
    phone_number: str
    pin: Optional[str] = None

class WhatsAppRequest(BaseModel):
    recipient: str
    message: str
    pin: Optional[str] = None
    use_android: Optional[bool] = False

class LaunchAppRequest(BaseModel):
    app_name: str

class AndroidConnectRequest(BaseModel):
    ip_port: str

class GeminiChatRequest(BaseModel):
    message: str
    voice_enabled: bool = True

# ----------------- Root & HUD Web Page ----------------- #

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the primary JARVIS Holographic HUD frontend."""
    index_file = frontend_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_file)

# ----------------- Core REST Endpoints ----------------- #

@app.get("/api/status")
async def get_system_status():
    """Retrieve full system telemetry and connected hardware state."""
    telemetry = windows_controller.get_system_telemetry()
    android_devs = android_bridge.get_connected_devices()
    android_batt = android_bridge.get_android_battery() if android_devs else {"connected": False}
    
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "windows": telemetry,
        "android": {
            "adb_ready": android_bridge.is_adb_ready(),
            "devices": android_devs,
            "battery": android_batt
        },
        "ai_brain": {
            "provider": "Gemini",
            "model": settings.GEMINI_MODEL,
            "ready": gemini_brain.is_ready,
            "status": "online" if gemini_brain.is_ready else "offline — configure GEMINI_API_KEY in .env"
        }
    }

@app.post("/api/ai/clear-memory")
async def clear_ai_memory():
    """Clear Gemini AI multi-turn conversation memory."""
    gemini_brain.clear_memory()
    return {"success": True, "message": "Gemini AI conversation memory cleared."}

@app.get("/api/ai/status")
async def get_ai_status():
    """Get Gemini AI Brain status and configuration."""
    return {
        "provider": "Google Gemini",
        "model": settings.GEMINI_MODEL,
        "ready": gemini_brain.is_ready,
        "api_key_set": bool(settings.GEMINI_API_KEY),
        "max_history": settings.GEMINI_MAX_HISTORY,
        "get_api_key_url": "https://aistudio.google.com/apikey"
    }

@app.post("/api/command")
async def execute_command(req: CommandRequest):
    """Execute text or transcribed voice command."""
    # Process through Intent Engine
    res = await intent_engine.process_command(req.command, pin=req.pin)

    # Generate Neural Voice Audio if requested
    audio_data = None
    if req.voice_enabled and res.get("response_text"):
        audio_data = await voice_engine.speak_text_async(res["response_text"])

    return {
        "command": req.command,
        "intent": res.get("intent"),
        "response_text": res.get("response_text"),
        "data": res.get("data"),
        "audio": audio_data
    }

@app.post("/api/speak")
async def text_to_speech(req: SpeakRequest):
    """Convert arbitrary text into Neural Speech audio."""
    res = await voice_engine.speak_text_async(req.text, voice=req.voice)
    return res

@app.get("/api/voices")
async def list_voices():
    """List available AI voices."""
    return {"voices": voice_engine.get_available_voices(), "current": settings.DEFAULT_TTS_VOICE}

# ----------------- Camera Endpoints ----------------- #

@app.post("/api/camera/photo")
async def capture_photo():
    """Capture snapshot from camera."""
    return camera_service.capture_photo()

@app.get("/api/camera/stream")
def stream_camera():
    """Live MJPEG video feed for HUD."""
    return StreamingResponse(
        camera_service.generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# ----------------- Notes Endpoints ----------------- #

@app.get("/api/notes")
def get_notes(search: Optional[str] = None):
    """List notes with optional search query."""
    return {"notes": notes_manager.list_notes(search=search)}

@app.post("/api/notes")
def create_note(req: NoteCreateRequest):
    """Save new note or dictation."""
    return notes_manager.add_note(content=req.content, title=req.title, category=req.category or "general")

@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int):
    """Delete a note by ID."""
    return notes_manager.delete_note(note_id)

@app.get("/api/notes/export")
def export_notes():
    """Export all notes as Markdown."""
    return {"markdown": notes_manager.export_all_notes()}

# ----------------- Communications (Calls & WhatsApp) ----------------- #

@app.post("/api/phone/call")
def make_call(req: CallRequest):
    """Initiate a phone call via Android bridge or mobile dial intent."""
    require_pin_auth(req.pin)
    return android_bridge.initiate_phone_call(req.phone_number)

@app.post("/api/whatsapp/send")
def send_whatsapp(req: WhatsAppRequest):
    """Send WhatsApp message."""
    require_pin_auth(req.pin)
    return whatsapp_social_service.send_whatsapp(req.recipient, req.message, use_android=req.use_android or False)

# ----------------- App Launcher & Android Controls ----------------- #

@app.post("/api/app/launch")
def launch_application(req: LaunchAppRequest):
    """Launch application on Windows or Android."""
    win_res = windows_controller.launch_app(req.app_name)
    if win_res["success"]:
        return win_res
    if android_bridge.is_adb_ready() and android_bridge.get_connected_devices():
        return android_bridge.launch_android_app(req.app_name)
    return win_res

@app.get("/api/android/devices")
def list_android_devices():
    """List connected Android devices."""
    return {
        "adb_ready": android_bridge.is_adb_ready(),
        "devices": android_bridge.get_connected_devices()
    }

@app.post("/api/android/connect")
def connect_android_wireless(req: AndroidConnectRequest):
    """Pair wireless Android device via ADB."""
    return android_bridge.connect_wireless(req.ip_port)

# ----------------- Real-Time WebSocket Gateway ----------------- #

@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """Real-time bi-directional voice and control socket."""
    await websocket.accept()
    logger.info("Client connected to SUVI WebSocket.")

    # Send welcome handshake
    await websocket.send_json({
        "type": "handshake",
        "status": "connected",
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION
    })

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type", "command")

            if msg_type == "command" or msg_type == "voice_transcript":
                query_text = data.get("text", "")
                pin = data.get("pin")
                
                # Emit thinking/processing state
                await websocket.send_json({"type": "state", "status": "processing"})

                # Execute through Intent Engine
                res = await intent_engine.process_command(query_text, pin=pin)
                response_text = res.get("response_text", "")

                # Generate Neural Voice Audio
                audio_res = None
                if response_text:
                    audio_res = await voice_engine.speak_text_async(response_text)

                # Return full response packet
                await websocket.send_json({
                    "type": "response",
                    "query": query_text,
                    "intent": res.get("intent"),
                    "response_text": response_text,
                    "data": res.get("data"),
                    "audio": audio_res
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "time": os.times()})

    except WebSocketDisconnect:
        logger.info("Client disconnected from SUVI WebSocket.")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
