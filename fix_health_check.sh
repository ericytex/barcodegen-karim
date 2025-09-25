#!/bin/bash

# Docker Health Check Fix Script
# This script rebuilds and restarts the container with the fixed health check

echo "🔧 Fixing Docker Container Health Check..."
echo "=========================================="

# Stop and remove existing container
echo "🛑 Stopping existing container..."
docker-compose down

# Remove the old image to force rebuild
echo "🗑️  Removing old image..."
docker image rm barcodegen-karim-barcode-api 2>/dev/null || echo "Image not found, continuing..."

# Rebuild the container
echo "🔨 Rebuilding container with health check fix..."
docker-compose build --no-cache

# Start the container
echo "🚀 Starting container..."
docker-compose up -d

# Wait a moment for startup
echo "⏳ Waiting for container to start..."
sleep 10

# Check container status
echo "📊 Container Status:"
docker ps --filter "name=barcode-generator-api"

# Test health check
echo ""
echo "🏥 Testing health check..."
sleep 5

# Test the new health endpoint
echo "Testing /healthz endpoint..."
curl -f http://localhost:8034/healthz && echo "✅ Health check passed!" || echo "❌ Health check failed!"

echo ""
echo "📋 Next steps:"
echo "1. Wait 2-3 minutes for health check to stabilize"
echo "2. Run 'docker ps' to verify container shows 'healthy' status"
echo "3. If still unhealthy, check logs with 'docker logs barcode-generator-api'"
echo ""
echo "✅ Health check fix deployment complete!"
