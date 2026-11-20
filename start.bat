@echo off
title TruthLens System Launcher
echo ========================================================
echo Launching TruthLens AI Misinformation Detection System
echo ========================================================

set "ROOT_DIR=%~dp0"

echo 1. Launching TruthLens Backend Engine (Port 8000)...
start "TruthLens Backend" cmd.exe /c "call "%ROOT_DIR%run_backend.bat""

echo Waiting for Backend initialization...
timeout /t 3 /nobreak >nul

echo 2. Launching TruthLens Frontend Dashboard (Port 5173)...
start "TruthLens Frontend" cmd.exe /c "call "%ROOT_DIR%run_frontend.bat""

echo.
echo ========================================================
echo TruthLens System is Active!
echo.
echo   * Web Dashboard:  http://localhost:5173
echo   * Backend Docs:   http://127.0.0.1:8000/docs
echo   * Health Check:   http://127.0.0.1:8000/health
echo.
echo Two windows have been opened for the Backend and Frontend.
echo Closing this window will not stop the running servers.
echo ========================================================
echo.
timeout /t 5
