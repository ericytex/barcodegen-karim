#!/bin/bash
# Barcode Generator API Startup Script

echo "🚀 Starting Barcode Generator API..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "../barcode_env" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source ../barcode_env/bin/activate

# Install API dependencies if needed
echo "📦 Checking API dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Start the API server
echo "🌐 Starting FastAPI server on http://localhost:8034"
echo "📚 API Documentation: http://localhost:8034/docs"
echo "🔍 ReDoc Documentation: http://localhost:8034/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

uvicorn app:app --host 0.0.0.0 --port 8034 --reload
