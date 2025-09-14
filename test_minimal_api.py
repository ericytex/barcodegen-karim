#!/usr/bin/env python3
"""
Minimal API test to verify security works
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, status, Request, Depends

# Set environment variables
os.environ['API_KEYS'] = 'frontend-api-key-12345,your-super-secret-api-key-here'

# Import security
from security_deps import security_manager, verify_api_key, check_rate_limit

# Create minimal app
app = FastAPI(title="Test API")

@app.get("/api/health")
async def health_check(
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    return {"status": "healthy", "message": "Security working!"}

@app.post("/api/barcodes/generate")
async def generate_barcodes(
    request: dict,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    return {"success": True, "message": "Barcodes generated!", "data": request}

if __name__ == "__main__":
    print("🚀 Starting minimal test API...")
    print(f"API Keys: {security_manager.api_keys}")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
