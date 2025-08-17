#!/usr/bin/env python3
"""
Test script to verify that exception handling works correctly
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from fastapi import HTTPException, status
from app.api.auth import register
from app.models.auth import UserRegister


async def test_register_exception():
    """Test that HTTPException details are preserved"""
    print("Testing exception handling...")
    
    # Create a mock user data
    user_data = UserRegister(
        email="test@example.com",
        password="testpassword",
        full_name="Test User"
    )
    
    try:
        # This should raise an HTTPException if user already exists
        result = await register(user_data)
        print(f"✅ Registration successful: {result}")
    except HTTPException as e:
        print(f"✅ HTTPException caught correctly:")
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: '{e.detail}'")
        print(f"   Detail is empty: {e.detail == ''}")
        
        if e.detail != "":
            print("✅ SUCCESS: Exception detail is preserved!")
        else:
            print("❌ FAILURE: Exception detail is empty!")
    except Exception as e:
        print(f"❌ Unexpected exception: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_register_exception())
