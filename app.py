"""
Barcode Generator API
FastAPI application for generating barcode labels
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import asyncio
from datetime import datetime

# Import our models and services
from models.barcode_models import (
    BarcodeGenerationRequest, 
    BarcodeGenerationResponse,
    FileUploadResponse,
    FileListResponse,
    ErrorResponse,
    HealthResponse
)
from services.barcode_service import BarcodeService
from services.archive_manager import ArchiveManager
from models.database import DatabaseManager
from utils.file_utils import save_uploaded_file, list_files_in_directory, cleanup_old_files, get_safe_filename
from security_deps import security_manager, verify_api_key, check_rate_limit

# Initialize FastAPI app
app = FastAPI(
    title="Barcode Generator API",
    description="Secure API for generating barcode labels with IMEI, model info, and QR codes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS securely
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,https://barcode-gene-frontend.vercel.app,https://barcode-gene-frontend-hmnff9rd3-ericytexs-projects.vercel.app,https://barcelona-cleaners-birthday-deleted.trycloudflare.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security middleware disabled for now - using decorators instead
# app.add_middleware(SecurityMiddleware)

# Initialize barcode service
barcode_service = BarcodeService()
archive_manager = ArchiveManager()
db_manager = DatabaseManager()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    print("🚀 Starting Barcode Generator API...")
    # Clean up old files on startup
    cleanup_old_files("uploads", max_age_hours=24)
    cleanup_old_files("downloads/barcodes", max_age_hours=24)
    cleanup_old_files("downloads/pdfs", max_age_hours=24)
    print("✅ API startup complete!")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check(
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime="running"
    )

# Generate barcodes from JSON data
@app.post("/barcodes/generate", response_model=BarcodeGenerationResponse)
async def generate_barcodes(
    request: BarcodeGenerationRequest,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Generate barcodes from JSON data"""
    try:
        # Convert Pydantic models to dictionaries
        items = [item.dict() for item in request.items]
        
        # Generate barcodes
        generated_files = await barcode_service.generate_barcodes_from_data(
            items,
            auto_generate_second_imei=request.auto_generate_second_imei
        )
        
        # Extract files and session_id from the response
        if isinstance(generated_files, tuple):
            files, session_id = generated_files
        else:
            files = generated_files
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not generated_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No barcodes were generated. Please check your input data."
            )
        
        # Create PDF if requested
        pdf_file = None
        if request.create_pdf:
            print(f"📄 Creating PDF with {len(files)} barcodes...")
            pdf_file = barcode_service.create_pdf_from_barcodes(
                pdf_filename=None,
                grid_cols=request.pdf_grid_cols,
                grid_rows=request.pdf_grid_rows,
                session_id=session_id
            )
            print(f"📄 PDF creation result: {pdf_file}")
        
        return BarcodeGenerationResponse(
            success=True,
            message=f"Successfully generated {len(files)} barcodes",
            generated_files=files,
            pdf_file=pdf_file,
            total_items=len(files)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating barcodes: {str(e)}"
        )

# Upload Excel file and generate barcodes
@app.post("/barcodes/upload-excel", response_model=BarcodeGenerationResponse)
async def upload_excel_and_generate(
    file: UploadFile = File(...),
    create_pdf: bool = True,
    pdf_grid_cols: int = 5,
    pdf_grid_rows: int = 12,
    auto_generate_second_imei: bool = True,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Upload Excel file and generate barcodes"""
    try:
        # Security validations
        if not security_manager.validate_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only Excel files (.xlsx, .xls) are allowed"
            )
        
        if not security_manager.validate_file_size(file.size):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 10MB"
            )
        
        # Sanitize filename
        safe_filename = security_manager.sanitize_filename(file.filename)
        
        # Validate file type
        if not safe_filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Excel files (.xlsx, .xls) are supported"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Save uploaded file with sanitized filename
        file_path = await save_uploaded_file(file_content, safe_filename)
        
        # Generate barcodes from Excel
        # Generate barcodes from Excel
        # Read inside service and pass flag through a temporary read to items
        # to reuse the same code path
        generated_files = []
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            
            # Debug: Print column names and first few rows
            print(f"📊 Excel file columns: {list(df.columns)}")
            print(f"📊 Excel file shape: {df.shape}")
            print(f"📊 First 3 rows:")
            print(df.head(3).to_string())
            
            items = df.to_dict('records')
            generated_files = await barcode_service.generate_barcodes_from_data(
                items,
                auto_generate_second_imei=auto_generate_second_imei
            )
            
            # Extract files and session_id from the response
            if isinstance(generated_files, tuple):
                files, session_id = generated_files
            else:
                files = generated_files
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🔍 Generated files count: {len(files)}")
            print(f"🔍 Generated files: {files}")
            print(f"🔍 Session ID: {session_id}")
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read Excel: {str(e)}"
            )
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No barcodes were generated from the Excel file. Please check the file format and data."
            )
        
        # Create PDF if requested
        pdf_file = None
        if create_pdf:
            pdf_file = barcode_service.create_pdf_from_barcodes(
                grid_cols=pdf_grid_cols,
                grid_rows=pdf_grid_rows,
                session_id=session_id
            )
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        return BarcodeGenerationResponse(
            success=True,
            message=f"Successfully generated {len(files)} barcodes from Excel file",
            generated_files=files,
            pdf_file=pdf_file,
            total_items=len(files)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Excel file: {str(e)}"
        )

# List all generated files
@app.get("/barcodes/list", response_model=FileListResponse)
async def list_generated_files(
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """List all generated barcode and PDF files"""
    try:
        # List PNG files
        png_files = list_files_in_directory("downloads/barcodes", [".png"])
        
        # List PDF files
        pdf_files = list_files_in_directory("downloads/pdfs", [".pdf"])
        
        # Combine all files
        all_files = png_files + pdf_files
        
        return FileListResponse(
            success=True,
            files=all_files,
            total_count=len(all_files)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing files: {str(e)}"
        )

# Download individual PNG file
@app.get("/barcodes/download/{filename}")
async def download_barcode_file(
    filename: str,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Download a generated barcode PNG file"""
    try:
        # Sanitize filename to prevent path traversal
        safe_filename = security_manager.sanitize_filename(filename)
        file_path = os.path.join("downloads/barcodes", safe_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=safe_filename,
            media_type="image/png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )

# Download PDF file
@app.get("/barcodes/download-pdf/{filename}")
async def download_pdf_file(filename: str):
    """Download a generated PDF file"""
    try:
        # Sanitize filename
        safe_filename = get_safe_filename(filename)
        file_path = os.path.join("downloads/pdfs", safe_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=safe_filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading PDF: {str(e)}"
        )

# Create PDF from existing barcodes
@app.post("/barcodes/create-pdf", response_model=BarcodeGenerationResponse)
async def create_pdf_from_existing(
    grid_cols: int = 5,
    grid_rows: int = 12,
    pdf_filename: Optional[str] = None
):
    """Create a PDF from existing barcode images"""
    try:
        pdf_file = barcode_service.create_pdf_from_barcodes(
            pdf_filename=pdf_filename,
            grid_cols=grid_cols,
            grid_rows=grid_rows
        )
        
        if not pdf_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No barcode images found to create PDF"
            )
        
        return BarcodeGenerationResponse(
            success=True,
            message="PDF created successfully from existing barcodes",
            generated_files=[],
            pdf_file=pdf_file,
            total_items=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating PDF: {str(e)}"
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Barcode Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "generate_barcodes": "/api/barcodes/generate",
            "upload_excel": "/api/barcodes/upload-excel",
            "list_files": "/api/barcodes/list",
            "download_file": "/api/barcodes/download/{filename}",
            "download_pdf": "/api/barcodes/download-pdf/{filename}",
            "create_pdf": "/api/barcodes/create-pdf"
        }
    }

# Database and Archive Management Endpoints

@app.get("/archive/sessions", response_model=dict)
async def get_archive_sessions(
    limit: int = 10,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Get recent archive sessions"""
    try:
        sessions = archive_manager.list_archive_sessions(limit)
        return {"success": True, "sessions": sessions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get archive sessions: {str(e)}"
        )

@app.get("/archive/session/{session_id}/files", response_model=dict)
async def get_session_files(
    session_id: str,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Get all files from a specific archive session"""
    try:
        files = archive_manager.get_session_files(session_id)
        return {"success": True, "files": files, "session_id": session_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session files: {str(e)}"
        )

@app.get("/archive/statistics", response_model=dict)
async def get_archive_statistics(
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Get archive statistics"""
    try:
        stats = archive_manager.get_archive_statistics()
        return {"success": True, "statistics": stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get archive statistics: {str(e)}"
        )

@app.get("/database/files", response_model=dict)
async def get_all_files(
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Get all files from database"""
    try:
        files = db_manager.get_all_files()
        return {"success": True, "files": files, "total_count": len(files)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get files: {str(e)}"
        )

@app.get("/database/file/{filename}", response_model=dict)
async def get_file_by_name(
    filename: str,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(check_rate_limit)
):
    """Get specific file by filename"""
    try:
        file_data = db_manager.get_file_by_filename(filename)
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found"
            )
        return {"success": True, "file": file_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
