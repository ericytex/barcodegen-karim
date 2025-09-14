#!/bin/bash

# Production deployment script for Barcode Generator API

set -e

echo "🚀 Starting Barcode Generator API Production Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p downloads/barcodes downloads/pdfs logs uploads

# Set proper permissions
chmod -R 755 downloads logs uploads

# Build the Docker image
print_status "Building Docker image..."
docker build -t barcode-generator-api:latest .

# Stop any existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Start the service
print_status "Starting Barcode Generator API..."
docker-compose up -d

# Wait for the service to be ready
print_status "Waiting for service to be ready..."
sleep 10

# Check if the service is running (with API key for authenticated endpoints)
if curl -f -H "X-API-Key: frontend-api-key-12345" http://localhost:8000/api/health > /dev/null 2>&1; then
    print_status "✅ Barcode Generator API is running successfully!"
    echo ""
    echo "🌐 API Endpoints:"
    echo "   - Health Check: http://localhost:8000/api/health"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - ReDoc Documentation: http://localhost:8000/redoc"
    echo "   - Generate Barcodes: http://localhost:8000/api/barcodes/generate"
    echo "   - Upload Excel: http://localhost:8000/api/barcodes/upload-excel"
    echo "   - Database Files: http://localhost:8000/api/database/files"
    echo "   - Archive Statistics: http://localhost:8000/api/archive/statistics"
    echo ""
    echo "🔐 Security:"
    echo "   - API Key required for most endpoints"
    echo "   - Default API Key: frontend-api-key-12345"
    echo "   - Rate limiting enabled"
    echo "   - CORS configured for frontend"
    echo ""
    echo "📁 Generated files will be saved to:"
    echo "   - PNG files: ./downloads/barcodes/"
    echo "   - PDF files: ./downloads/pdfs/"
    echo "   - Archives: ./archives/"
    echo "   - Database: ./data/barcode_generator.db"
    echo "   - Logs: ./logs/"
    echo ""
    echo "🔧 Management commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - Stop service: docker-compose down"
    echo "   - Restart service: docker-compose restart"
    echo "   - View database: sqlite3 ./data/barcode_generator.db"
else
    print_error "❌ Service failed to start. Check logs with: docker-compose logs"
    exit 1
fi
