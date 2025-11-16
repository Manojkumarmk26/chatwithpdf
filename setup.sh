#!/bin/bash

echo "================================"
echo "Setting up Intelligent Doc Chat"
echo "================================"

# Create directories
mkdir -p backend frontend uploads cache faiss_indices

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Setup frontend
echo "Installing Node dependencies..."
cd frontend
npm install
cd ..

echo "✅ Setup complete!"
echo ""
echo "To run the application:"
echo "1. Backend: python -m uvicorn backend.main:app --reload"
echo "2. Frontend: cd frontend && npm start"
