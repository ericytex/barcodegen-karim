"""
File utility functions for the Barcode Generator API
"""

import os
import aiofiles
from typing import List, Dict, Any
from datetime import datetime
import mimetypes


async def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str = "uploads") -> str:
    """Save uploaded file to the uploads directory"""
    # Create upload directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file asynchronously
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    return file_path


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get file information"""
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    
    return {
        "filename": os.path.basename(file_path),
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "mime_type": mime_type or "application/octet-stream"
    }


def list_files_in_directory(directory: str, extensions: List[str] = None) -> List[Dict[str, Any]]:
    """List files in a directory with optional extension filtering"""
    if not os.path.exists(directory):
        return []
    
    files = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            # Filter by extensions if provided
            if extensions:
                _, ext = os.path.splitext(filename)
                if ext.lower() not in extensions:
                    continue
            
            file_info = get_file_info(file_path)
            files.append(file_info)
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: x.get("modified", ""), reverse=True)
    return files


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """Clean up files older than specified hours"""
    if not os.path.exists(directory):
        return 0
    
    current_time = datetime.now().timestamp()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except OSError:
                    pass  # Skip files that can't be deleted
    
    return cleaned_count


def get_safe_filename(filename: str) -> str:
    """Get a safe filename by removing/replacing unsafe characters"""
    import re
    # Remove or replace unsafe characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    safe_filename = safe_filename.strip(' .')
    # Ensure filename is not empty
    if not safe_filename:
        safe_filename = "file"
    return safe_filename
