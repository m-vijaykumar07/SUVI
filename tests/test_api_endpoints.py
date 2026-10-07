import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.main import app

client = TestClient(app)

def test_frontend_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "SUVI //" in response.text
    print("[+] GET / (Holographic HUD) returns 200 OK")

def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "windows" in data
    assert "android" in data
    print("[+] GET /api/status returns telemetry data")

def test_command_endpoint():
    response = client.post("/api/command", json={"command": "what time is it", "voice_enabled": False})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "TIME"
    print(f"[+] POST /api/command responded with: '{data['response_text']}'")

def test_notes_endpoints():
    # Create note
    res_create = client.post("/api/notes", json={"content": "Test endpoint note", "title": "API Test"})
    assert res_create.status_code == 200
    note_id = res_create.json()["id"]

    # Get notes
    res_get = client.get("/api/notes?search=API Test")
    assert res_get.status_code == 200
    assert len(res_get.json()["notes"]) >= 1

    # Delete note
    res_del = client.delete(f"/api/notes/{note_id}")
    assert res_del.status_code == 200
    print("[+] Notes REST endpoints (POST, GET, DELETE) functioning perfectly")

if __name__ == "__main__":
    print("==================================================")
    print("       SUVI FastAPI Endpoints Verification        ")
    print("==================================================")
    test_frontend_index()
    test_status_endpoint()
    test_command_endpoint()
    test_notes_endpoints()
    print("==================================================")
    print("       ALL API ENDPOINTS FUNCTIONING 100%         ")
    print("==================================================")
