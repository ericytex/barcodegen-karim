"""
Pydantic models for Barcode Generator API
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BarcodeItem(BaseModel):
    """Individual barcode item model"""
    imei: str = Field(..., description="IMEI/Serial number")
    box_id: Optional[str] = Field(None, description="Box ID number")
    model: str = Field(..., description="Product model")
    product: Optional[str] = Field(None, description="Full product description (e.g., 'SMART 8 64+3 SHINY GOLD')")
    color: Optional[str] = Field(None, description="Product color (extracted from product if not provided)")
    dn: str = Field(default="M8N7", description="D/N number")


class BarcodeGenerationRequest(BaseModel):
    """Request model for generating barcodes from JSON data"""
    items: List[BarcodeItem] = Field(..., description="List of barcode items to generate")
    create_pdf: bool = Field(default=True, description="Whether to create PDF after generation")
    pdf_grid_cols: int = Field(default=5, description="Number of columns in PDF grid")
    pdf_grid_rows: int = Field(default=12, description="Number of rows in PDF grid")
    auto_generate_second_imei: bool = Field(default=True, description="If true, generate a second IMEI (replacing Box ID) keeping first 8 digits and randomizing last 7 with uniqueness across runs")


class BarcodeGenerationResponse(BaseModel):
    """Response model for barcode generation"""
    success: bool
    message: str
    generated_files: List[str] = Field(default_factory=list, description="List of generated PNG files")
    pdf_file: Optional[str] = Field(None, description="Generated PDF file path")
    total_items: int
    timestamp: datetime = Field(default_factory=datetime.now)


class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    filename: str
    file_size: int
    content_type: str
    timestamp: datetime = Field(default_factory=datetime.now)


class FileListResponse(BaseModel):
    """Response model for listing files"""
    success: bool
    files: List[dict] = Field(default_factory=list, description="List of available files")
    total_count: int
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    uptime: Optional[str] = None
