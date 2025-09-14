"""
Archive Manager for Barcode Generator
Handles moving files to timestamped archive folders instead of deleting them
"""

import os
import shutil
import glob
from datetime import datetime
from typing import List, Dict, Any
from models.database import DatabaseManager, BarcodeRecord


class ArchiveManager:
    def __init__(self, base_archive_dir: str = "archives"):
        self.base_archive_dir = base_archive_dir
        self.db_manager = DatabaseManager()
        self.ensure_archive_directory()
    
    def ensure_archive_directory(self):
        """Ensure the archive directory exists"""
        os.makedirs(self.base_archive_dir, exist_ok=True)
    
    def create_archive_session(self) -> str:
        """Create a new archive session with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"
        archive_path = os.path.join(self.base_archive_dir, session_id)
        os.makedirs(archive_path, exist_ok=True)
        return session_id, archive_path
    
    def archive_files(self, barcode_dir: str, pdf_dir: str, 
                     generation_session: str, file_metadata: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Archive files from barcode and PDF directories to timestamped folders
        
        Args:
            barcode_dir: Directory containing PNG files
            pdf_dir: Directory containing PDF files
            generation_session: Session ID for this generation
            file_metadata: Optional metadata for files (IMEI, Box ID, etc.)
        
        Returns:
            Dictionary with archive statistics
        """
        print("📦 Starting file archiving process...")
        
        # Create archive session
        session_id, archive_path = self.create_archive_session()
        
        # Create subdirectories
        png_archive_path = os.path.join(archive_path, "barcodes")
        pdf_archive_path = os.path.join(archive_path, "pdfs")
        os.makedirs(png_archive_path, exist_ok=True)
        os.makedirs(pdf_archive_path, exist_ok=True)
        
        archived_files = []
        total_size = 0
        png_count = 0
        pdf_count = 0
        
        # Archive PNG files
        png_files = glob.glob(os.path.join(barcode_dir, "*.png"))
        print(f"📁 Found {len(png_files)} PNG files to archive")
        
        for png_file in png_files:
            filename = os.path.basename(png_file)
            archive_file_path = os.path.join(png_archive_path, filename)
            
            try:
                # Move file to archive
                shutil.move(png_file, archive_file_path)
                
                # Get file size
                file_size = os.path.getsize(archive_file_path)
                total_size += file_size
                png_count += 1
                
                # Find metadata for this file if provided
                metadata = self._find_file_metadata(filename, file_metadata)
                
                # Create database record
                record = BarcodeRecord(
                    filename=filename,
                    file_path=png_file,  # Original path
                    archive_path=archive_file_path,
                    file_type="png",
                    file_size=file_size,
                    created_at=datetime.now().isoformat(),
                    archived_at=datetime.now().isoformat(),
                    generation_session=session_id,
                    imei=metadata.get("imei"),
                    box_id=metadata.get("box_id"),
                    model=metadata.get("model"),
                    product=metadata.get("product"),
                    color=metadata.get("color"),
                    dn=metadata.get("dn")
                )
                
                record_id = self.db_manager.insert_barcode_record(record)
                archived_files.append({
                    "id": record_id,
                    "filename": filename,
                    "type": "png",
                    "size": file_size,
                    "archive_path": archive_file_path
                })
                
                print(f"✅ Archived PNG: {filename}")
                
            except Exception as e:
                print(f"❌ Failed to archive {filename}: {e}")
        
        # Archive PDF files
        pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
        print(f"📁 Found {len(pdf_files)} PDF files to archive")
        
        for pdf_file in pdf_files:
            filename = os.path.basename(pdf_file)
            archive_file_path = os.path.join(pdf_archive_path, filename)
            
            try:
                # Move file to archive
                shutil.move(pdf_file, archive_file_path)
                
                # Get file size
                file_size = os.path.getsize(archive_file_path)
                total_size += file_size
                pdf_count += 1
                
                # Create database record
                record = BarcodeRecord(
                    filename=filename,
                    file_path=pdf_file,  # Original path
                    archive_path=archive_file_path,
                    file_type="pdf",
                    file_size=file_size,
                    created_at=datetime.now().isoformat(),
                    archived_at=datetime.now().isoformat(),
                    generation_session=session_id,
                    imei=None,  # PDFs don't have individual IMEI
                    box_id=None,
                    model=None,
                    product=None,
                    color=None,
                    dn=None
                )
                
                record_id = self.db_manager.insert_barcode_record(record)
                archived_files.append({
                    "id": record_id,
                    "filename": filename,
                    "type": "pdf",
                    "size": file_size,
                    "archive_path": archive_file_path
                })
                
                print(f"✅ Archived PDF: {filename}")
                
            except Exception as e:
                print(f"❌ Failed to archive {pdf_file}: {e}")
        
        # Record generation session
        session_record_id = self.db_manager.insert_generation_session(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            total_files=len(archived_files),
            png_count=png_count,
            pdf_count=pdf_count,
            total_size=total_size,
            excel_filename=None,  # Could be passed as parameter
            notes=f"Archived {png_count} PNG files and {pdf_count} PDF files"
        )
        
        print(f"📦 Archive completed!")
        print(f"   Session ID: {session_id}")
        print(f"   Archive Path: {archive_path}")
        print(f"   Total Files: {len(archived_files)}")
        print(f"   PNG Files: {png_count}")
        print(f"   PDF Files: {pdf_count}")
        print(f"   Total Size: {total_size / 1024 / 1024:.2f} MB")
        
        return {
            "session_id": session_id,
            "archive_path": archive_path,
            "archived_files": archived_files,
            "total_files": len(archived_files),
            "png_count": png_count,
            "pdf_count": pdf_count,
            "total_size": total_size,
            "session_record_id": session_record_id
        }
    
    def _find_file_metadata(self, filename: str, file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find metadata for a specific file"""
        if not file_metadata:
            return {}
        
        # Extract IMEI from filename (assuming format: barcode_label_IMEI_number.png)
        try:
            parts = filename.split("_")
            if len(parts) >= 3:
                imei = parts[2]  # Extract IMEI from filename
                # Find matching metadata
                for metadata in file_metadata:
                    if metadata.get("imei") == imei:
                        return metadata
        except Exception:
            pass
        
        return {}
    
    def get_archive_statistics(self) -> Dict[str, Any]:
        """Get archive statistics"""
        return self.db_manager.get_statistics()
    
    def list_archive_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent archive sessions"""
        return self.db_manager.get_recent_sessions(limit)
    
    def get_session_files(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all files from a specific session"""
        return self.db_manager.get_files_by_session(session_id)
