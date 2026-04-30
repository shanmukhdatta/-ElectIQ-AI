#!/bin/bash
# ElectIQ - Quick Start Script

echo ""
echo "ElectIQ - Election Intelligence Assistant"
echo "============================================"
echo ""

if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Add your GROQ_API_KEY to .env before continuing!"
    echo "Optional fallback: add GOOGLE_API_KEY for Gemini."
    echo ""
fi

if ! command -v python3 &>/dev/null; then
    echo "Python 3 not found. Please install Python 3.10+"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt -q

export $(grep -v '^#' .env | xargs)

echo ""
echo "Starting ElectIQ on http://localhost:5000"
echo "============================================"
echo ""

python3 -m backend.app
