@echo off
title TruthLens Frontend Dashboard [Port 5173]
echo ========================================================
echo Starting TruthLens React Frontend UI (Port 5173)...
echo ========================================================

cd /d "%~dp0frontend"

where npm.cmd >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where npm >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] npm was not found. Please ensure Node.js is installed.
        pause
        exit /b 1
    )
)

echo.
echo ========================================================
echo TruthLens Dashboard starting at http://localhost:5173
echo Press Ctrl+C to stop the dev server.
echo ========================================================
echo.

call npm.cmd run dev
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Frontend dev server terminated.
    pause
)
