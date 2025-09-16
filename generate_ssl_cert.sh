#!/bin/bash

# Generate Self-Signed SSL Certificate for Barcode Generator API
# This script creates a self-signed certificate for HTTPS support

echo "🔐 Generating Self-Signed SSL Certificate..."

# Create certificates directory if it doesn't exist
mkdir -p certificates

# Generate private key
echo "📝 Creating private key..."
openssl genrsa -out certificates/server.key 2048

# Generate certificate signing request
echo "📝 Creating certificate signing request..."
openssl req -new -key certificates/server.key -out certificates/server.csr -subj "/C=US/ST=State/L=City/O=BarcodeGenerator/OU=IT/CN=194.163.134.129"

# Generate self-signed certificate
echo "📝 Creating self-signed certificate..."
openssl x509 -req -days 365 -in certificates/server.csr -signkey certificates/server.key -out certificates/server.crt

# Set proper permissions
chmod 600 certificates/server.key
chmod 644 certificates/server.crt

echo "✅ SSL Certificate generated successfully!"
echo ""
echo "📁 Files created:"
echo "   - certificates/server.key (private key)"
echo "   - certificates/server.crt (certificate)"
echo ""
echo "🔧 To use HTTPS:"
echo "   1. Update your FastAPI app to use SSL"
echo "   2. Update frontend to use https://194.163.134.129:8034"
echo "   3. Accept the self-signed certificate in browsers"
echo ""
echo "⚠️  Note: Browsers will show a security warning for self-signed certificates."
echo "   This is normal and expected for development/testing purposes."
