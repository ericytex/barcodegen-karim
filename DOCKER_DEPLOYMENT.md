# Docker Deployment Guide for Barcode Generator API

## 🐳 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 512MB RAM available
- Port 8000 available

### One-Command Deployment
```bash
./deploy.sh
```

This script will:
- Build the Docker image
- Create necessary directories
- Start the API service
- Verify the deployment

## 📋 Manual Deployment

### 1. Build the Docker Image
```bash
docker build -t barcode-generator-api:latest .
```

### 2. Create Required Directories
```bash
mkdir -p downloads/barcodes downloads/pdfs logs uploads data archives
chmod -R 755 downloads logs uploads data archives
```

### 3. Start with Docker Compose
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
curl -H "X-API-Key: frontend-api-key-12345" http://localhost:8000/api/health
```

## 🔧 Configuration

### Environment Variables
The API uses the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 8000 | Port for the API server |
| `API_HOST` | 0.0.0.0 | Host to bind the server |
| `WORKERS` | 1 | Number of worker processes |
| `LOG_LEVEL` | INFO | Logging level |
| `MAX_FILE_SIZE` | 10485760 | Maximum file upload size (10MB) |

### Volume Mounts
The following directories are mounted for persistence:

- `./downloads` → `/app/downloads` - Generated barcodes and PDFs
- `./logs` → `/app/logs` - Application logs
- `./data` → `/app/data` - SQLite database
- `./archives` → `/app/archives` - Archived files
- `./uploads` → `/app/uploads` - Temporary uploads

## 🌐 API Endpoints

### Public Endpoints
- `GET /api/health` - Health check
- `GET /docs` - API documentation
- `GET /redoc` - ReDoc documentation

### Authenticated Endpoints (Require X-API-Key header)
- `POST /api/barcodes/generate` - Generate barcodes from data
- `POST /api/barcodes/upload-excel` - Upload Excel file and generate barcodes
- `GET /api/barcodes/list` - List generated files
- `GET /api/barcodes/download/{filename}` - Download files
- `GET /api/database/files` - Get database files with metadata
- `GET /api/archive/statistics` - Get archive statistics
- `GET /api/archive/sessions` - Get archive sessions

### Default API Key
- **Key**: `frontend-api-key-12345`
- **Header**: `X-API-Key: frontend-api-key-12345`

## 🔐 Security Features

- **API Key Authentication**: All endpoints except health check require API key
- **Rate Limiting**: Prevents abuse with configurable limits
- **CORS Protection**: Configured for frontend integration
- **File Upload Security**: Validates file types and sizes
- **Non-root User**: Container runs as non-root user for security

## 📊 Monitoring

### Health Check
```bash
curl -H "X-API-Key: frontend-api-key-12345" http://localhost:8000/api/health
```

### View Logs
```bash
docker-compose logs -f
```

### Database Access
```bash
sqlite3 ./data/barcode_generator.db
```

### Container Status
```bash
docker-compose ps
```

## 🔄 Management Commands

### Start Service
```bash
docker-compose up -d
```

### Stop Service
```bash
docker-compose down
```

### Restart Service
```bash
docker-compose restart
```

### Update Service
```bash
docker-compose down
docker build -t barcode-generator-api:latest .
docker-compose up -d
```

### View Resource Usage
```bash
docker stats barcode-generator-api
```

## 📁 File Structure

```
api/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker build instructions
├── docker-compose.yml    # Docker Compose configuration
├── deploy.sh            # Deployment script
├── env.production       # Production environment variables
├── services/            # Business logic services
├── models/              # Data models and database
├── downloads/           # Generated files (mounted)
├── logs/               # Application logs (mounted)
├── data/               # SQLite database (mounted)
├── archives/           # Archived files (mounted)
└── uploads/            # Temporary uploads (mounted)
```

## 🚨 Troubleshooting

### Service Won't Start
1. Check if port 8000 is available: `lsof -i :8000`
2. Check Docker logs: `docker-compose logs`
3. Verify Docker is running: `docker ps`

### API Returns 401 Unauthorized
- Ensure you're including the API key header: `X-API-Key: frontend-api-key-12345`

### Database Issues
- Check if data directory exists and has proper permissions
- Verify SQLite database file: `ls -la ./data/`

### File Upload Issues
- Check upload directory permissions: `chmod 755 ./uploads`
- Verify file size limits in environment variables

### Performance Issues
- Monitor resource usage: `docker stats`
- Check logs for errors: `docker-compose logs -f`
- Consider increasing memory limits in docker-compose.yml

## 🔧 Customization

### Changing API Key
1. Update the API key in your frontend configuration
2. Restart the service: `docker-compose restart`

### Modifying Resource Limits
Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G      # Increase memory limit
      cpus: '1.0'     # Increase CPU limit
```

### Adding Environment Variables
Add to `docker-compose.yml`:
```yaml
environment:
  - CUSTOM_VAR=value
```

## 📈 Production Considerations

### Scaling
- Use multiple workers: Set `WORKERS=4` in environment
- Use load balancer for multiple instances
- Consider Redis for session storage

### Backup
- Regular backup of `./data` directory (database)
- Backup of `./downloads` directory (generated files)
- Backup of `./archives` directory (archived files)

### Monitoring
- Set up health check monitoring
- Monitor disk space usage
- Set up log aggregation
- Monitor API response times

### Security
- Change default API key in production
- Use HTTPS in production
- Set up proper firewall rules
- Regular security updates

## 🆘 Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Verify configuration files
3. Check Docker and Docker Compose versions
4. Review this documentation

---

**Deployment Status**: ✅ Production Ready
**Last Updated**: September 2025
**Version**: 1.0.0
