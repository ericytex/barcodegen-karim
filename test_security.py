#!/usr/bin/env python3
"""
Simple test script to verify security implementation
"""

import os
import sys
sys.path.append('.')

# Set environment variables
os.environ['API_KEYS'] = 'frontend-api-key-12345,your-super-secret-api-key-here'

from security import security_manager

def test_security():
    print("🔒 Testing Security Implementation")
    print("=" * 50)
    
    # Test API key validation
    print("1. Testing API Key Validation:")
    valid_key = "frontend-api-key-12345"
    invalid_key = "invalid-key"
    
    print(f"   Valid key '{valid_key}': {security_manager.validate_api_key(valid_key)}")
    print(f"   Invalid key '{invalid_key}': {security_manager.validate_api_key(invalid_key)}")
    
    # Test rate limiting
    print("\n2. Testing Rate Limiting:")
    test_ip = "127.0.0.1"
    for i in range(5):
        result = security_manager.check_rate_limit(test_ip)
        print(f"   Request {i+1}: {result}")
    
    # Test file validation
    print("\n3. Testing File Validation:")
    valid_file = "test.xlsx"
    invalid_file = "test.txt"
    
    print(f"   Valid file '{valid_file}': {security_manager.validate_file_type(valid_file)}")
    print(f"   Invalid file '{invalid_file}': {security_manager.validate_file_type(invalid_file)}")
    
    # Test filename sanitization
    print("\n4. Testing Filename Sanitization:")
    dangerous_filename = "../../../etc/passwd"
    safe_filename = security_manager.sanitize_filename(dangerous_filename)
    print(f"   Dangerous: '{dangerous_filename}' -> Safe: '{safe_filename}'")
    
    print("\n✅ Security tests completed!")

if __name__ == "__main__":
    test_security()
