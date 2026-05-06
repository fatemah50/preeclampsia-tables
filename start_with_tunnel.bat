@echo off
REM PrediCare - Start Streamlit with ngrok tunnel for network sharing
echo.
echo ================================================================
echo    PrediCare: Preeclampsia Risk Predictor v3.0
echo    Starting with Network Tunnel (ngrok)
echo ================================================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ngrok not found. Installing...
    pip install pyngrok
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install pyngrok. Please install manually:
        echo   pip install pyngrok
        pause
        exit /b 1
    )
)

REM Optional: Set ngrok authtoken (get from https://dashboard.ngrok.com/auth)
REM Uncomment and replace YOUR_TOKEN with your actual token for persistent URLs
REM ngrok config add-authtoken YOUR_TOKEN

echo.
echo Starting Streamlit app...
echo Once Streamlit is running, ngrok will create a tunnel.
echo.
echo You will see a URL like: https://xxxx-xx-xxx-xxx-xx.ngrok.io
echo Share this URL with network users to access PrediCare.
echo.
echo Press Ctrl+C to stop both services.
echo.

REM Start Streamlit
streamlit run app.py

pause
