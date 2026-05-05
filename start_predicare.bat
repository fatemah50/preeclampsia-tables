@echo off
REM PrediCare Streamlit startup script
SET "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
SET "VENV_PY=%SCRIPT_DIR%.venv\Scripts\python.exe"
IF EXIST "%VENV_PY%" (
  start "" "%VENV_PY%" -m streamlit run "%SCRIPT_DIR%app.py" --server.port=8501 --server.address=0.0.0.0 --server.headless=true --logger.level=error
) ELSE (
  start "" python -m streamlit run "%SCRIPT_DIR%app.py" --server.port=8501 --server.address=0.0.0.0 --server.headless=true --logger.level=error
)
