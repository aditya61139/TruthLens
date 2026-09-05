@echo off
title TruthLens System Launcher
echo ========================================================
echo Launching TruthLens AI Fact-Checking System...
echo ========================================================

echo 1. Launching Backend on http://127.0.0.1:8000 ...
start "TruthLens Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo 2. Launching Frontend on http://localhost:5173 ...
start "TruthLens Frontend" cmd /k "cd /d %~dp0\frontend && call npm.cmd run dev"

echo.
echo TruthLens is starting!
echo - Web Dashboard: http://localhost:5173
echo - Backend API Docs: http://127.0.0.1:8000/docs
echo.
