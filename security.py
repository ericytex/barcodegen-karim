"""
Security utilities for Barcode Generator API
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from functools import wraps
import time
from collections import defaultdict

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(list)

class SecurityManager:
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.jwt_secret = os.getenv("JWT_SECRET", "your-jwt-secret-key")
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
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        # Clean old entries
        rate_limit_storage[client_ip] = [
            timestamp for timestamp in rate_limit_storage[client_ip]
            if timestamp > window_start
        ]
        
        # Check if limit exceeded
        if len(rate_limit_storage[client_ip]) >= self.rate_limit_requests:
            return False
        
        # Add current request
        rate_limit_storage[client_ip].append(current_time)
        return True
    
    def generate_jwt_token(self, user_id: str, expires_hours: int = 24) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def validate_jwt_token(self, token: str) -> Optional[dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
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

# Security decorators
def require_api_key(func):
    """Decorator to require API key authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the Request object in the arguments
        request = None
        for arg in args:
            if hasattr(arg, 'headers') and hasattr(arg, 'client'):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
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
        
        return await func(*args, **kwargs)
    return wrapper

def rate_limit(func):
    """Decorator to implement rate limiting"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the Request object in the arguments
        request = None
        for arg in args:
            if hasattr(arg, 'headers') and hasattr(arg, 'client'):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        client_ip = request.client.host
        
        if not security_manager.check_rate_limit(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return await func(*args, **kwargs)
    return wrapper

def secure_file_upload(func):
    """Decorator to secure file uploads"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Additional file validation can be added here
        return await func(request, *args, **kwargs)
    return wrapper

# Security middleware
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add security headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    
                    # Add security headers
                    security_headers = [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"x-xss-protection", b"1; mode=block"),
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
                    ]
                    
                    # Add CSP header if enabled
                    if os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true":
                        csp = os.getenv("CONTENT_SECURITY_POLICY", "default-src 'self'")
                        security_headers.append((b"content-security-policy", csp.encode()))
                    
                    headers.extend(security_headers)
                    message["headers"] = headers
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
