#!/bin/bash
# Streamlit Deployment Script for PrediCare
# macOS/Linux Version

echo "========================================"
echo "PrediCare - Preeclampsia Risk Predictor"
echo "Streamlit Version"
echo "========================================"
echo ""

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "✗ Virtual environment not found"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "========================================"
echo "Starting Streamlit Server..."
echo "========================================"
echo ""
echo "App will be available at:"
echo "  Local:   http://localhost:8501"
echo "  Network: Check terminal for network URL"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0
