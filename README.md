# Barcode Generator API

A FastAPI-based REST API for generating barcode labels with IMEI, model info, and QR codes.

## Features

- **JSON Data Input**: Generate barcodes from JSON data
- **Excel File Upload**: Upload Excel files and generate barcodes automatically
- **Color Extraction**: Automatically extract colors from product descriptions
- **PDF Generation**: Create PDF collections with configurable grid layouts
- **File Management**: List, download, and manage generated files
- **Async Processing**: Non-blocking file operations
- **Auto Documentation**: Swagger UI and ReDoc documentation

## Installation

### Development Setup

1. **Install Dependencies**:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Run the API**:
   ```bash
   python app.py
   ```
   
   Or with uvicorn directly:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Production Deployment with Docker

1. **Quick Deploy**:
   ```bash
   cd api
   ./deploy.sh
   ```

2. **Manual Docker Build**:
   ```bash
   cd api
   docker build -t barcode-generator-api:latest .
   docker run -p 8000:8000 barcode-generator-api:latest
   ```

3. **Docker Compose**:
   ```bash
   cd api
   docker-compose up -d
   ```

4. **Production Environment**:
   - Copy `env.production` to `.env` and adjust settings
   - Use `docker-compose -f docker-compose.yml --env-file .env up -d`

### Production Features

- **Font Support**: Uses Liberation Sans fonts (Linux-compatible)
- **Security**: Non-root user, proper file permissions
- **Health Checks**: Built-in health monitoring
- **Resource Limits**: Memory and CPU constraints
- **Persistent Storage**: Volumes for downloads, logs, uploads
- **Port 8000**: Consistent port configuration

## API Endpoints

### Health Check
- **GET** `/api/health` - Check API health status

### Barcode Generation
- **POST** `/api/barcodes/generate` - Generate barcodes from JSON data
- **POST** `/api/barcodes/upload-excel` - Upload Excel file and generate barcodes

### File Management
- **GET** `/api/barcodes/list` - List all generated files
- **GET** `/api/barcodes/download/{filename}` - Download PNG file
- **GET** `/api/barcodes/download-pdf/{filename}` - Download PDF file
- **POST** `/api/barcodes/create-pdf` - Create PDF from existing barcodes

## Usage Examples

### 1. Generate Barcodes from JSON

```bash
curl -X POST "http://localhost:8000/api/barcodes/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "imei": "359827134443046",
        "box_id": "355760833587361",
        "model": "X6525D",
        "product": "SMART 8 64+3 SHINY GOLD",
        "dn": "M8N7"
      }
    ],
    "create_pdf": true,
    "pdf_grid_cols": 5,
    "pdf_grid_rows": 12
  }'
```

### 2. Upload Excel File

```bash
curl -X POST "http://localhost:8000/api/barcodes/upload-excel" \
  -F "file=@barcode_data.xlsx" \
  -F "create_pdf=true" \
  -F "pdf_grid_cols=5" \
  -F "pdf_grid_rows=12"
```

### 3. List Generated Files

```bash
curl -X GET "http://localhost:8000/api/barcodes/list"
```

### 4. Download Files

```bash
# Download PNG file
curl -X GET "http://localhost:8000/api/barcodes/download/barcode_label_359827134443046_1.png" \
  --output barcode.png

# Download PDF file
curl -X GET "http://localhost:8000/api/barcodes/download-pdf/barcode_collection_20250907_162720.pdf" \
  --output barcodes.pdf
```

## Data Models

### BarcodeItem
```json
{
  "imei": "string (required)",
  "box_id": "string (optional)",
  "model": "string (required)",
  "product": "string (optional)",
  "color": "string (optional)",
  "dn": "string (default: M8N7)"
}
```

### BarcodeGenerationRequest
```json
{
  "items": [BarcodeItem],
  "create_pdf": "boolean (default: true)",
  "pdf_grid_cols": "integer (default: 5)",
  "pdf_grid_rows": "integer (default: 12)"
}
```

## Excel File Format

The Excel file should contain the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| imei | IMEI/Serial number | 359827134443046 |
| box_id | Box ID number | 355760833587361 |
| model | Product model | X6525D |
| product | Full product description | SMART 8 64+3 SHINY GOLD |
| dn | D/N number | M8N7 |

**Note**: The `product` column is used to automatically extract the color. If not provided, you can use a separate `color` column.

## File Structure

```
api/
├── app.py                 # Main FastAPI application
├── models/                # Pydantic models
│   └── barcode_models.py
├── services/              # Business logic
│   └── barcode_service.py
├── utils/                 # Utility functions
│   └── file_utils.py
├── uploads/               # Temporary file uploads
├── downloads/             # Generated files
│   ├── barcodes/         # PNG files
│   └── pdfs/             # PDF files
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Configuration

### Environment Variables
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: False)

### File Cleanup
The API automatically cleans up old files:
- Upload files: 24 hours
- Generated files: 24 hours

## Error Handling

The API returns structured error responses:

```json
{
  "success": false,
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2025-09-07T16:27:20.123456"
}
```

## Development

### Running in Development Mode
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest
```

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

This project is part of the Barcode Generator system.
