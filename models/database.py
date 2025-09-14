"""
SQLite Database Models for Barcode Generator
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BarcodeRecord:
    id: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    archive_path: str = ""
    file_type: str = ""  # 'png' or 'pdf'
    file_size: int = 0
    created_at: str = ""
    archived_at: str = ""
    generation_session: str = ""
    imei: Optional[str] = None
    box_id: Optional[str] = None
    model: Optional[str] = None
    product: Optional[str] = None
    color: Optional[str] = None
    dn: Optional[str] = None


class DatabaseManager:
    def __init__(self, db_path: str = "data/barcode_generator.db"):
        self.db_path = db_path
        self.ensure_database_directory()
        self.init_database()
    
    def ensure_database_directory(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create barcode_files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS barcode_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    archive_path TEXT NOT NULL,
                    file_type TEXT NOT NULL CHECK (file_type IN ('png', 'pdf')),
                    file_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    archived_at TEXT NOT NULL,
                    generation_session TEXT NOT NULL,
                    imei TEXT,
                    box_id TEXT,
                    model TEXT,
                    product TEXT,
                    color TEXT,
                    dn TEXT,
                    created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create generation_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generation_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    total_files INTEGER NOT NULL,
                    png_count INTEGER NOT NULL,
                    pdf_count INTEGER NOT NULL,
                    total_size INTEGER NOT NULL,
                    excel_filename TEXT,
                    notes TEXT,
                    created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON barcode_files(filename)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_type ON barcode_files(file_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_generation_session ON barcode_files(generation_session)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON barcode_files(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON generation_sessions(session_id)")
            
            conn.commit()
    
    def insert_barcode_record(self, record: BarcodeRecord) -> int:
        """Insert a new barcode record and return the ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO barcode_files (
                    filename, file_path, archive_path, file_type, file_size,
                    created_at, archived_at, generation_session, imei, box_id,
                    model, product, color, dn
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.filename, record.file_path, record.archive_path,
                record.file_type, record.file_size, record.created_at,
                record.archived_at, record.generation_session, record.imei,
                record.box_id, record.model, record.product, record.color, record.dn
            ))
            conn.commit()
            return cursor.lastrowid
    
    def insert_generation_session(self, session_id: str, created_at: str, 
                                total_files: int, png_count: int, pdf_count: int,
                                total_size: int, excel_filename: str = None, 
                                notes: str = None) -> int:
        """Insert a new generation session record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO generation_sessions (
                    session_id, created_at, total_files, png_count, pdf_count,
                    total_size, excel_filename, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, created_at, total_files, png_count, pdf_count, 
                  total_size, excel_filename, notes))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all barcode files with their metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM barcode_files 
                ORDER BY created_timestamp DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_files_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all files from a specific generation session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM barcode_files 
                WHERE generation_session = ?
                ORDER BY created_timestamp DESC
            """, (session_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent generation sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM generation_sessions 
                ORDER BY created_timestamp DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_file_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get a specific file by filename"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM barcode_files 
                WHERE filename = ?
            """, (filename,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total files
            cursor.execute("SELECT COUNT(*) FROM barcode_files")
            total_files = cursor.fetchone()[0]
            
            # PNG files
            cursor.execute("SELECT COUNT(*) FROM barcode_files WHERE file_type = 'png'")
            png_count = cursor.fetchone()[0]
            
            # PDF files
            cursor.execute("SELECT COUNT(*) FROM barcode_files WHERE file_type = 'pdf'")
            pdf_count = cursor.fetchone()[0]
            
            # Total size
            cursor.execute("SELECT SUM(file_size) FROM barcode_files")
            total_size = cursor.fetchone()[0] or 0
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) FROM generation_sessions")
            total_sessions = cursor.fetchone()[0]
            
            return {
                "total_files": total_files,
                "png_count": png_count,
                "pdf_count": pdf_count,
                "total_size": total_size,
                "total_sessions": total_sessions
            }
