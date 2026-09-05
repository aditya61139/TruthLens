@echo off
title TruthLens Frontend Dashboard
echo ========================================================
echo Starting TruthLens React Frontend UI (Port 5173)...
echo ========================================================
cd /d "%~dp0\frontend"
call npm.cmd run dev
pause
