@echo off
title SUVI - Smart Unified Voice Intelligence
color 0b

echo =======================================================================
echo         SUVI (Smart Unified Voice Intelligence) // JARVIS CORE
echo =======================================================================
echo.

cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv" (
    echo [*] Setting up Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [*] Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: Create .env if not exists
if not exist ".env" (
    echo [*] Initializing .env configuration from template...
    copy .env.example .env
)

echo.
echo [+] Core Systems Initialized.
echo [+] Starting SUVI Server on http://localhost:8000 (accessible on Android via local IP)
echo.

:: Open browser after 2 seconds
start "" cmd /c "timeout /t 2 >nul & start http://localhost:8000"

:: Run FastAPI server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
