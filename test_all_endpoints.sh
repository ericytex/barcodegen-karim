#!/bin/bash

echo "🧪 Testing All Barcode API Endpoints..."
echo "========================================"

API_KEY="frontend-api-key-12345"
BASE_URL_LOCAL="http://localhost:8000"
BASE_URL_HTTPS="https://barcelona-cleaners-birthday-deleted.trycloudflare.com"

echo ""
echo "🔍 Testing LOCAL endpoints (new format without /api):"
echo "----------------------------------------------------"

echo "1. Health endpoint (new):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_LOCAL/health" | jq . || echo "❌ Failed"

echo ""
echo "2. Health endpoint (old):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_LOCAL/api/health" | jq . || echo "❌ Failed"

echo ""
echo "3. Barcodes list (new):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_LOCAL/barcodes/list" | jq . || echo "❌ Failed"

echo ""
echo "4. Barcodes list (old):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_LOCAL/api/barcodes/list" | jq . || echo "❌ Failed"

echo ""
echo "🌐 Testing HTTPS endpoints (via Cloudflare Tunnel):"
echo "--------------------------------------------------"

echo "5. Health endpoint HTTPS (new):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_HTTPS/health" | jq . || echo "❌ Failed"

echo ""
echo "6. Health endpoint HTTPS (old):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_HTTPS/api/health" | jq . || echo "❌ Failed"

echo ""
echo "7. Barcodes list HTTPS (new):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_HTTPS/barcodes/list" | jq . || echo "❌ Failed"

echo ""
echo "8. Barcodes list HTTPS (old):"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL_HTTPS/api/barcodes/list" | jq . || echo "❌ Failed"

echo ""
echo "📊 Testing POST endpoints (upload simulation):"
echo "--------------------------------------------"

echo "9. Generate barcodes (new):"
curl -s -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"items":[{"imei":"123456789012345","model":"Test Model","box_id":"BOX001"}],"create_pdf":false}' \
  "$BASE_URL_LOCAL/barcodes/generate" | jq . || echo "❌ Failed"

echo ""
echo "10. Generate barcodes (old):"
curl -s -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"items":[{"imei":"123456789012345","model":"Test Model","box_id":"BOX001"}],"create_pdf":false}' \
  "$BASE_URL_LOCAL/api/barcodes/generate" | jq . || echo "❌ Failed"

echo ""
echo "✅ Testing complete!"
echo "==================="
