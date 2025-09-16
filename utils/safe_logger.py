"""
Safe logging utility for the backend API
Removes sensitive data in production environments
"""

import os
import logging
from typing import Any, Dict, List, Optional

class SafeLogger:
    def __init__(self):
        self.is_production = os.getenv('ENVIRONMENT', 'development') == 'production'
        self.debug_enabled = os.getenv('DEBUG', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Remove sensitive information from data"""
        if isinstance(data, str):
            # Remove API keys, tokens, and sensitive URLs
            sensitive_patterns = [
                r'api[_-]?key[_-]?[a-zA-Z0-9_-]+',
                r'token[_-]?[a-zA-Z0-9_-]+',
                r'password[_-]?[a-zA-Z0-9_-]+',
                r'secret[_-]?[a-zA-Z0-9_-]+',
                r'key[_-]?[a-zA-Z0-9_-]+',
            ]
            
            import re
            for pattern in sensitive_patterns:
                data = re.sub(pattern, '[REDACTED]', data, flags=re.IGNORECASE)
            
            return data
        
        if isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in ['key', 'token', 'password', 'secret']):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        
        return data
    
    def info(self, message: str, data: Optional[Any] = None):
        """Log info message"""
        if data is not None:
            sanitized_data = self._sanitize_data(data) if self.is_production else data
            self.logger.info(f"{message}: {sanitized_data}")
        else:
            self.logger.info(message)
    
    def debug(self, message: str, data: Optional[Any] = None):
        """Log debug message (only in debug mode)"""
        if not self.debug_enabled:
            return
        
        if data is not None:
            self.logger.debug(f"{message}: {data}")
        else:
            self.logger.debug(message)
    
    def warning(self, message: str, data: Optional[Any] = None):
        """Log warning message"""
        if data is not None:
            sanitized_data = self._sanitize_data(data) if self.is_production else data
            self.logger.warning(f"{message}: {sanitized_data}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, data: Optional[Any] = None):
        """Log error message"""
        if data is not None:
            sanitized_data = self._sanitize_data(data) if self.is_production else data
            self.logger.error(f"{message}: {sanitized_data}")
        else:
            self.logger.error(message)
    
    def print(self, message: str, data: Optional[Any] = None):
        """Print message (for backward compatibility)"""
        if self.is_production:
            self.info(message, data)
        else:
            if data is not None:
                print(f"{message}: {data}")
            else:
                print(message)

# Global safe logger instance
safe_logger = SafeLogger()
