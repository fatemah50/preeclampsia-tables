

@echo off
REM Streamlit Deployment Script for PrediCare
REM This script starts the Streamlit app with proper configuration

echo ========================================
echo PrediCare - Preeclampsia Risk Predictor
echo Streamlit Version
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
echo Starting Streamlit Server...
echo ========================================
echo.
echo App will be available at:
echo   Local:   http://localhost:8501
echo   Network: Check terminal for network URL
echo.
echo Press Ctrl+C to stop the server
echo.

python -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0

pause
