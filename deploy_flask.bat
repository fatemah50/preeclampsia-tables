@echo off
REM Flask Deployment Script for PrediCare
REM This script starts the Flask app with proper configuration

echo ========================================
echo PrediCare - Preeclampsia Risk Predictor
echo Flask Version
echo ========================================
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✓ Virtual environment activated
) else (
    echo ✗ Virtual environment not found
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

echo.
echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo ========================================
echo Starting Flask Server...
echo ========================================
echo.
echo App will be available at:
echo   Local:   http://127.0.0.1:5000
echo   Network: Check terminal for network URLs
echo.
echo Press Ctrl+C to stop the server
echo.

set FLASK_APP=web_app.py
set FLASK_ENV=production
python web_app.py

pause
