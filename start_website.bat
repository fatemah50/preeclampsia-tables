@echo off
REM PrediCare Website Startup Script

echo.
echo ========================================
echo    PrediCare - Website Startup
echo ========================================
echo.

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found!
    echo Please create it first with: python -m venv .venv
    pause
    exit /b 1
)

echo.
echo Starting PrediCare website server...
echo.
echo The website will be available at:
echo   Local: http://localhost:5000
echo   To find your IP address, open Command Prompt and type: ipconfig
echo.
echo Press Ctrl+C to stop the server
echo.

python web_app.py

pause
