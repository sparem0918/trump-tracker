@echo off
chcp 65001 > nul
setlocal

echo ============================================================
echo Trump Impact Tracker - Local Server
echo ============================================================

REM Check Python
where python > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check/create venv
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo [SETUP] Checking dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

REM Run app
echo.
echo ============================================================
echo Server starting...
echo Open in browser: http://localhost:5001
echo Press Ctrl+C to stop.
echo ============================================================
echo.
python app.py

pause
