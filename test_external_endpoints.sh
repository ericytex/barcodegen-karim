#!/bin/bash

echo "🌐 Testing External Barcode API Endpoints"
echo "=========================================="

API_KEY="frontend-api-key-12345"
TUNNEL_URL="https://barcelona-cleaners-birthday-deleted.trycloudflare.com"

echo ""
echo "🔍 Testing NEW endpoints (without /api):"
echo "----------------------------------------"

echo "1. Health endpoint (new):"
curl -s -H "X-API-Key: $API_KEY" "$TUNNEL_URL/health" | jq . || echo "❌ Failed"

echo ""
echo "2. Barcodes list (new):"
curl -s -H "X-API-Key: $API_KEY" "$TUNNEL_URL/barcodes/list" | jq . || echo "❌ Failed"

echo ""
echo "🔍 Testing OLD endpoints (with /api - backward compatibility):"
echo "--------------------------------------------------------------"

echo "3. Health endpoint (old):"
curl -s -H "X-API-Key: $API_KEY" "$TUNNEL_URL/api/health" | jq . || echo "❌ Failed"

echo ""
echo "4. Barcodes list (old):"
curl -s -H "X-API-Key: $API_KEY" "$TUNNEL_URL/api/barcodes/list" | jq . || echo "❌ Failed"

echo ""
echo "📊 Testing POST endpoints:"
echo "------------------------"

echo "5. Generate barcodes (new):"
curl -s -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"items":[{"imei":"123456789012345","model":"Test Model","box_id":"BOX001"}],"create_pdf":false}' \
  "$TUNNEL_URL/barcodes/generate" | jq . || echo "❌ Failed"

echo ""
echo "6. Generate barcodes (old):"
curl -s -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"items":[{"imei":"123456789012345","model":"Test Model","box_id":"BOX001"}],"create_pdf":false}' \
  "$TUNNEL_URL/api/barcodes/generate" | jq . || echo "❌ Failed"

echo ""
echo "🔍 Testing Frontend Integration URLs:"
echo "------------------------------------"

echo "7. Frontend should call these URLs:"
echo "   - POST $TUNNEL_URL/barcodes/upload-excel"
echo "   - GET  $TUNNEL_URL/barcodes/list"
echo "   - GET  $TUNNEL_URL/health"

echo ""
echo "✅ External testing complete!"
echo "============================="
