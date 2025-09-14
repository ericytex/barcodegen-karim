#!/usr/bin/env python3
"""
Test script to verify the API works with security
"""

import os
import sys
sys.path.append('.')

# Set environment variables
os.environ['API_KEYS'] = 'frontend-api-key-12345,your-super-secret-api-key-here'

def test_api_import():
    print("🔧 Testing API Import...")
    try:
        from app import app
        print("✅ App imported successfully")
        
        from security_deps import security_manager, verify_api_key
        print("✅ Security dependencies imported successfully")
        
        print(f"API Keys loaded: {security_manager.api_keys}")
        print(f"Validating test key: {security_manager.validate_api_key('frontend-api-key-12345')}")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_fastapi_app():
    print("\n🚀 Testing FastAPI App...")
    try:
        from app import app
        
        # Test if we can get the routes
        routes = [route.path for route in app.routes]
        print(f"Available routes: {routes}")
        
        return True
    except Exception as e:
        print(f"❌ FastAPI test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 API Security Test")
    print("=" * 50)
    
    success = test_api_import()
    if success:
        test_fastapi_app()
    
    print("\n✅ Test completed!")
