@echo off
REM PrediCare - One-Click Network Launcher
REM This script automatically starts Streamlit with ngrok tunnel

cd /d "%~dp0"

echo.
echo ================================================================
echo    PrediCare: Preeclampsia Risk Predictor v3.0
echo    Network Tunnel Launcher
echo ================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo Visit: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo [INFO] Installing dependencies...
python -m pip install pyngrok streamlit -q

REM Start the tunnel
echo [INFO] Starting PrediCare with network tunnel...
echo.
python start_network_tunnel.py

pause
