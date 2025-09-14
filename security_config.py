# Security Configuration for Barcode Generator API

# Authentication & Authorization
API_KEY_REQUIRED=true
API_KEY_HEADER=X-API-Key
API_KEYS=your-secret-api-key-here,another-key-for-frontend

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE
CORS_ALLOW_HEADERS=*

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds

# File Upload Security
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=xlsx,xls,csv
UPLOAD_PATH_WHITELIST=/app/uploads

# Security Headers
SECURITY_HEADERS_ENABLED=true
CONTENT_SECURITY_POLICY=default-src 'self'

# Logging & Monitoring
LOG_SECURITY_EVENTS=true
LOG_FAILED_AUTH=true
LOG_FILE_UPLOADS=true

# Session Security
SESSION_SECRET=your-super-secret-session-key-change-this
SESSION_TIMEOUT=3600  # 1 hour

# Database Security (if implemented)
DB_ENCRYPTION_KEY=your-database-encryption-key
DB_CONNECTION_TIMEOUT=30
