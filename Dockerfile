# Production-ready Dockerfile for Barcode Generator API
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    API_PORT=8034

# Install system dependencies including fonts
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    libz-dev \
    curl \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy fonts
COPY fonts/ /app/fonts/
# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p uploads downloads/barcodes downloads/pdfs logs && \
    chmod -R 755 uploads downloads logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port 8034
EXPOSE 8034

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8034/api/health || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${API_PORT:-8034} --workers 1"]
