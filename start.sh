#!/bin/bash

# Transaction Reconciliation System Startup Script

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Transaction Reconciliation System - Startup Script      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Error: Python 3 is not installed."
    echo "  Please install Python 3 first."
    exit 1
fi

echo "✓ Python version: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "✗ Error: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "✗ Error: Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

# Check if required packages are installed
echo "📦 Checking dependencies..."
pip list | grep -q "fastapi" && {
    echo "✓ All required packages are installed"
} || {
    echo "📥 Installing required packages..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "✗ Error: Failed to install dependencies"
        exit 1
    fi
    echo "✓ Dependencies installed successfully"
}

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🚀 Starting Application Server...              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  📍 Web Interface: http://localhost:8000"
echo "  📍 API Docs:      http://localhost:8000/docs"
echo "  📍 ReDoc:         http://localhost:8000/redoc"
echo ""
echo "  Press Ctrl+C to stop the server"
echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

# Start the application
python main.py
