# Security Implementation Guide

## 🔒 Security Features Implemented

### 1. **API Key Authentication**
- All endpoints require `X-API-Key` header
- Multiple API keys supported for different clients
- Keys stored in environment variables

### 2. **Rate Limiting**
- 100 requests per minute per IP address
- Configurable limits via environment variables
- Prevents DoS attacks

### 3. **CORS Protection**
- Restricted to specific domains only
- No wildcard origins (`*`)
- Credentials support for authenticated requests

### 4. **File Upload Security**
- File type validation (only Excel files)
- File size limits (10MB max)
- Filename sanitization to prevent path traversal
- Secure file handling

### 5. **Security Headers**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HTTPS only)
- Content Security Policy

### 6. **Input Validation**
- Pydantic models for request validation
- File extension whitelist
- Path traversal prevention

## 🚀 Deployment Security

### Environment Variables (Required)
```bash
# Generate secure keys
API_KEYS=your-super-secret-api-key-here,frontend-api-key-12345
JWT_SECRET=$(openssl rand -base64 32)
SESSION_SECRET=$(openssl rand -base64 32)

# Restrict CORS to your domains
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security settings
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
MAX_FILE_SIZE=10485760
```

### Docker Security
- Non-root user execution
- Minimal base image (python:3.11-slim)
- No unnecessary packages
- Resource limits

## 🔧 Usage Examples

### Frontend Integration
```javascript
// Add API key to all requests
const apiKey = 'your-frontend-api-key';

fetch('http://localhost:8000/api/barcodes/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey
  },
  body: JSON.stringify(data)
});
```

### Testing with curl
```bash
# Generate barcodes
curl -X POST "http://localhost:8000/api/barcodes/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-super-secret-api-key-here" \
  -d '{"items": [{"imei": "123456789", "model": "X6525D"}]}'

# Upload Excel file
curl -X POST "http://localhost:8000/api/barcodes/upload-excel" \
  -H "X-API-Key: your-super-secret-api-key-here" \
  -F "file=@data.xlsx"
```

## ⚠️ Security Checklist

### Before Production:
- [ ] Change all default API keys
- [ ] Set strong JWT and session secrets
- [ ] Configure CORS origins to your domains only
- [ ] Enable HTTPS/TLS
- [ ] Set up proper logging and monitoring
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Backup and disaster recovery plan

### Monitoring:
- [ ] Log all authentication failures
- [ ] Monitor rate limit violations
- [ ] Track file upload attempts
- [ ] Alert on suspicious activity

## 🛡️ Additional Security Recommendations

### 1. **HTTPS/TLS**
```bash
# Use reverse proxy (nginx/traefik) with SSL
# Or configure FastAPI with SSL certificates
```

### 2. **Database Security** (if implemented)
- Encrypt sensitive data
- Use connection pooling
- Regular backups
- Access controls

### 3. **Logging & Monitoring**
- Centralized logging
- Security event alerts
- Performance monitoring
- Error tracking

### 4. **Network Security**
- Firewall rules
- VPN access for admin
- Network segmentation
- DDoS protection

## 🔍 Security Testing

### Test API Key Protection
```bash
# Should fail without API key
curl -X POST "http://localhost:8000/api/barcodes/generate" \
  -H "Content-Type: application/json" \
  -d '{"items": []}'
# Expected: 401 Unauthorized
```

### Test Rate Limiting
```bash
# Make 101 requests quickly
for i in {1..101}; do
  curl -X GET "http://localhost:8000/api/health" \
    -H "X-API-Key: your-api-key"
done
# Expected: 429 Too Many Requests after 100 requests
```

### Test File Upload Security
```bash
# Try uploading non-Excel file
curl -X POST "http://localhost:8000/api/barcodes/upload-excel" \
  -H "X-API-Key: your-api-key" \
  -F "file=@malicious.txt"
# Expected: 400 Bad Request
```
