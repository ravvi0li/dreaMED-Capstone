#!/bin/bash

# Quick Start Script for Pharmacovigilance App
# This script sets up and runs the application

set -e  # Exit on error

echo "🚀 Starting Pharmacovigilance App Setup..."
echo "=========================================="

# Check Python version
echo ""
echo "📌 Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo ""
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Check if database exists
if [ ! -f "pharma.db" ]; then
    echo ""
    echo "🗄️  Database not found. Running ETL pipeline..."
    python scripts/load_data.py
    echo "✓ Database created and populated"
else
    echo ""
    echo "✓ Database already exists"
fi

# Check if models exist
if [ ! -f "models/best_model.pkl" ]; then
    echo ""
    echo "🤖 Models not found. Training models..."
    echo "⚠️  This may take several minutes..."
    python scripts/train_model.py
    echo "✓ Models trained and saved"
else
    echo ""
    echo "✓ Models already exist"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created (edit SECRET_KEY for production)"
else
    echo ""
    echo "✓ .env file already exists"
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting Flask development server..."
echo "📍 Access the app at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Run the Flask app
export FLASK_ENV=development
python wsgi.py
