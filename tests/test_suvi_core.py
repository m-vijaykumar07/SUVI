import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings
from backend.security import verify_action_pin, sanitize_phone_number
from backend.services.windows_controller import windows_controller
from backend.services.notes_manager import notes_manager
from backend.services.intent_engine import intent_engine
from backend.services.voice_engine import voice_engine

def test_telemetry():
    print("[*] Testing System Telemetry...")
    stats = windows_controller.get_system_telemetry()
    assert "cpu" in stats, "Missing cpu stats"
    assert "ram" in stats, "Missing ram stats"
    assert "battery" in stats, "Missing battery stats"
    print(f"    [+] CPU: {stats['cpu']['percent']}%, RAM: {stats['ram']['percent']}%, Battery: {stats['battery']['percent']}%")

def test_notes_database():
    print("[*] Testing SQLite Notes Engine...")
    res = notes_manager.add_note("Meeting with team at 10 AM", title="Test Meeting")
    assert res["success"] is True, "Failed to create note"
    note_id = res["id"]

    notes = notes_manager.list_notes(search="Meeting")
    assert len(notes) >= 1, "Failed to search note"
    print(f"    [+] Created & retrieved note #{note_id}: {notes[0]['title']}")

    del_res = notes_manager.delete_note(note_id)
    assert del_res["success"] is True, "Failed to delete note"
    print(f"    [+] Deleted test note #{note_id}")

def test_security():
    print("[*] Testing Security & PIN Validation...")
    assert verify_action_pin("1234") is True, "Master PIN validation failed"
    assert verify_action_pin("wrong") is False, "Invalid PIN falsely approved"
    
    clean = sanitize_phone_number("+1 (234) 567-8901")
    assert clean == "+12345678901", f"Sanitization error: {clean}"
    print("    [+] Master PIN & Phone sanitization passed.")

async def test_intent_engine():
    print("[*] Testing Intent Engine parsing...")
    res1 = await intent_engine.process_command("who are you")
    assert res1["intent"] == "IDENTITY"
    print(f"    [+] 'who are you' -> {res1['intent']}")

    res2 = await intent_engine.process_command("system status")
    assert res2["intent"] == "TELEMETRY"
    print(f"    [+] 'system status' -> {res2['intent']}")

    res3 = await intent_engine.process_command("write note buy groceries tomorrow")
    assert res3["intent"] == "NOTE_CREATE"
    print(f"    [+] 'write note' -> {res3['intent']}")

    res4 = await intent_engine.process_command("volume up")
    assert res4["intent"] == "VOLUME"
    print(f"    [+] 'volume up' -> {res4['intent']}")

async def test_voice_synthesis():
    print("[*] Testing Neural TTS Speech Synthesis...")
    res = await voice_engine.speak_text_async("System initialized.")
    assert res["success"] is True, f"TTS generation failed: {res.get('error')}"
    print(f"    [+] TTS Audio generated: {res['audio_url']} (Cached: {res.get('cached')})")

async def main():
    print("==================================================")
    print("       SUVI Automated Test & Verification Suite    ")
    print("==================================================")
    test_telemetry()
    test_notes_database()
    test_security()
    await test_intent_engine()
    await test_voice_synthesis()
    print("==================================================")
    print("   ALL TESTS PASSED! SUVI CORE IS 100% HEALTHY    ")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
