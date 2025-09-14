"""
Simplified security implementation using FastAPI dependencies
"""

import os
from fastapi import HTTPException, status, Request, Depends
from typing import List

class SecurityManager:
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
    def _load_api_keys(self) -> List[str]:
        """Load API keys from environment"""
        keys_str = os.getenv("API_KEYS", "")
        return [key.strip() for key in keys_str.split(",") if key.strip()]
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        if not self.api_keys:
            return True  # No API keys configured, allow access
        return api_key in self.api_keys
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        # Simplified rate limiting - always allow for now
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        import os
        # Remove any path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate file type"""
        allowed_extensions = os.getenv("ALLOWED_FILE_TYPES", "xlsx,xls,csv").split(",")
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return file_ext in allowed_extensions
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size"""
        max_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
        return file_size <= max_size

# Global security manager instance
security_manager = SecurityManager()

# FastAPI dependency for API key validation
async def verify_api_key(request: Request):
    """Dependency to verify API key"""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if not security_manager.validate_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key

# FastAPI dependency for rate limiting
async def check_rate_limit(request: Request):
    """Dependency to check rate limiting"""
    client_ip = request.client.host
    
    if not security_manager.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return client_ip
