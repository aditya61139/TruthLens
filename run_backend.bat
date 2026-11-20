@echo off
title TruthLens Backend Server [Port 8000]
echo ========================================================
echo Starting TruthLens FastAPI Backend Engine (Port 8000)...
echo ========================================================

set "ROOT_DIR=%~dp0"
set "PYTHON_EXE="

:: 1. Check for project virtual environment
if exist "%ROOT_DIR%venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT_DIR%venv\Scripts\python.exe"
    echo [INFO] Detected project virtualenv: %ROOT_DIR%venv
    goto :found_python
)

:: 2. Check for user Python 3.11 install
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    echo [INFO] Detected Python 3.11: %PYTHON_EXE%
    goto :found_python
)

:: 3. Check for Windows Python launcher
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=py -3.11"
    echo [INFO] Using Windows Python Launcher: py -3.11
    goto :found_python
)

:: 4. Fallback to system PATH python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=python"
    echo [INFO] Using system PATH python
    goto :found_python
)

:python_not_found
echo.
echo [ERROR] Python was not found on your system!
echo Please ensure Python 3.11+ is installed or create a virtual environment in %ROOT_DIR%venv
echo.
pause
exit /b 1

:found_python
echo [INFO] Verifying backend dependencies...
%PYTHON_EXE% -c "import uvicorn, fastapi, sqlalchemy" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] Required packages not found with %PYTHON_EXE%.
    echo Attempting to install requirements...
    %PYTHON_EXE% -m pip install -r "%ROOT_DIR%backend\requirements.txt"
)

cd /d "%ROOT_DIR%backend"
echo.
echo ========================================================
echo TruthLens Backend is LIVE on http://127.0.0.1:8000
echo Swagger API Docs: http://127.0.0.1:8000/docs
echo Press Ctrl+C to stop the server.
echo ========================================================
echo.

%PYTHON_EXE% -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Backend terminated unexpectedly.
    pause
)
