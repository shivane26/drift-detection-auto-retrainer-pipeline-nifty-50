#!/bin/bash

# 🚀 Quick Render Deployment Script
# This script helps automate setup for local testing before Render deployment

echo "======================================"
echo "NIFTY50 MLOps Pipeline - Local Setup"
echo "======================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "✓ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Train model (if not exists)
if [ ! -f "app/models/ensemble.pkl" ]; then
    echo ""
    echo "✓ Training initial model (this may take 2-3 minutes)..."
    python3 app/train.py
else
    echo ""
    echo "✓ Model already trained, skipping training phase"
fi

# Run tests on endpoints
echo ""
echo "✓ Starting FastAPI server..."
echo "  Server will run on: http://127.0.0.1:8000"
echo "  Dashboard: http://127.0.0.1:8000/dashboard"
echo "  API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "To stop the server, press Ctrl+C"
echo ""

# Start the server
uvicorn app.app:app --host 127.0.0.1 --port 8000 --reload

echo ""
echo "======================================"
echo "Server stopped"
echo "======================================"
