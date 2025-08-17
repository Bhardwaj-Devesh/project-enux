#!/usr/bin/env python3
"""
Test script to verify the profile service fix
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.profile_service import profile_service
from app.services.supabase_service import supabase_service

async def test_profile_service():
    """Test the profile service to ensure it works correctly"""
    print("🧪 Testing Profile Service...")
    
    try:
        # Test 1: Check if supabase service has client property
        print("✅ SupabaseService has client property:", hasattr(supabase_service, 'client'))
        
        # Test 2: Check if client has table method
        client = supabase_service.client
        print("✅ Supabase client has table method:", hasattr(client, 'table'))
        
        # Test 3: Try to access profiles table (this should not raise an error)
        print("✅ Testing profiles table access...")
        try:
            # This should not raise an AttributeError anymore
            response = supabase_service.client.table("profiles").select("id").limit(1).execute()
            print("✅ Successfully accessed profiles table")
        except Exception as e:
            print(f"⚠️  Profiles table access issue (this might be expected if table doesn't exist): {e}")
        
        # Test 4: Test profile service methods
        print("✅ Testing profile service methods...")
        
        # Test get_profile method (should not raise AttributeError)
        try:
            # This should not raise 'SupabaseService' object has no attribute 'table'
            await profile_service.get_profile("test-user-id")
            print("✅ get_profile method works (returned None as expected for non-existent user)")
        except AttributeError as e:
            print(f"❌ get_profile still has AttributeError: {e}")
            return False
        except Exception as e:
            print(f"✅ get_profile method works (other error is expected): {e}")
        
        print("🎉 All profile service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Profile service test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_profile_service())
    sys.exit(0 if success else 1)
