@echo off
title TruthLens Backend Server
echo ========================================================
echo Starting TruthLens FastAPI Backend Engine (Port 8000)...
echo ========================================================
cd /d "%~dp0\backend"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
