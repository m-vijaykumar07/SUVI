@echo off
title Push SUVI to GitHub
color 0a

cd /d "%~dp0\.."
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe scripts\push_to_github.py
) else (
    python scripts\push_to_github.py
)

pause
