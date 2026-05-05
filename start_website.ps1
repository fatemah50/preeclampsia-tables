#!/usr/bin/env pwsh

# PrediCare Website Startup Script (PowerShell)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    PrediCare - Website Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path ".venv/Scripts/Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & ".venv/Scripts/Activate.ps1"
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first with: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting PrediCare website server..." -ForegroundColor Green
Write-Host ""
Write-Host "The website will be available at:" -ForegroundColor Cyan
Write-Host "  Local: http://localhost:5000" -ForegroundColor White
Write-Host "  To find your IP address, open Command Prompt and type: ipconfig" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python web_app.py

Read-Host "Press Enter to exit"
