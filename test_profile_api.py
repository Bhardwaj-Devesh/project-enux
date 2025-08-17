#!/usr/bin/env python3
"""
Test script for Profile API endpoints
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def get_auth_token() -> str:
    """Get authentication token for testing"""
    try:
        # First, try to register a user
        register_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Test User"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        
        # If registration fails (user might already exist), try to login
        if response.status_code != 200:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"❌ Failed to get auth token: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting auth token: {e}")
        return None

def test_get_profile(token: str) -> bool:
    """Test GET /profiles/me endpoint"""
    print("\n🔍 Testing GET /profiles/me...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/profiles/me", headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile retrieved successfully")
            print(f"   User ID: {profile.get('id')}")
            print(f"   Username: {profile.get('username')}")
            print(f"   Full Name: {profile.get('full_name')}")
            return True
        elif response.status_code == 404:
            print("ℹ️  Profile not found (expected for new user)")
            return True
        else:
            print(f"❌ Failed to get profile: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing get profile: {e}")
        return False

def test_update_profile(token: str) -> bool:
    """Test PUT /profiles/me endpoint"""
    print("\n✏️  Testing PUT /profiles/me...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    profile_data = {
        "full_name": "John Doe",
        "bio": "Full-stack developer passionate about React and Node.js",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "website": "https://johndoe.dev",
        "interests": ["React", "Node.js", "TypeScript", "Open Source"],
        "stage": "senior"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/profiles/me", headers=headers, json=profile_data)
        
        if response.status_code in [200, 201]:
            profile = response.json()
            print(f"✅ Profile updated successfully")
            print(f"   Full Name: {profile.get('full_name')}")
            print(f"   Company: {profile.get('company')}")
            print(f"   Stage: {profile.get('stage')}")
            print(f"   Interests: {profile.get('interests')}")
            return True
        else:
            print(f"❌ Failed to update profile: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing update profile: {e}")
        return False

def test_update_profile_partial(token: str) -> bool:
    """Test PUT /profiles/me with partial data"""
    print("\n🔄 Testing PUT /profiles/me (partial update)...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Only update bio and location
    profile_data = {
        "bio": "Updated bio - now working on AI and machine learning",
        "location": "New York, NY"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/profiles/me", headers=headers, json=profile_data)
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Partial profile update successful")
            print(f"   Bio: {profile.get('bio')}")
            print(f"   Location: {profile.get('location')}")
            return True
        else:
            print(f"❌ Failed to update profile partially: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing partial update: {e}")
        return False

def test_validation_errors(token: str) -> bool:
    """Test validation errors"""
    print("\n⚠️  Testing validation errors...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Test invalid stage
    invalid_data = {
        "stage": "invalid-stage"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/profiles/me", headers=headers, json=invalid_data)
        
        if response.status_code == 422:
            print("✅ Validation error caught for invalid stage")
            return True
        else:
            print(f"❌ Expected validation error, got: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing validation: {e}")
        return False

def test_search_profiles(token: str) -> bool:
    """Test GET /profiles/search endpoint"""
    print("\n🔍 Testing GET /profiles/search...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/profiles/search?query=developer&limit=5", headers=headers)
        
        if response.status_code == 200:
            profiles = response.json()
            print(f"✅ Search successful, found {len(profiles)} profiles")
            return True
        else:
            print(f"❌ Failed to search profiles: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False

def test_profiles_by_stage(token: str) -> bool:
    """Test GET /profiles/stage/{stage} endpoint"""
    print("\n👥 Testing GET /profiles/stage/senior...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/profiles/stage/senior?limit=5", headers=headers)
        
        if response.status_code == 200:
            profiles = response.json()
            print(f"✅ Stage search successful, found {len(profiles)} senior profiles")
            return True
        else:
            print(f"❌ Failed to get profiles by stage: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing stage search: {e}")
        return False

def main():
    """Run all profile API tests"""
    print("🚀 Starting Profile API Tests...")
    print("=" * 50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    print(f"✅ Authentication successful")
    
    # Run tests
    tests = [
        test_get_profile,
        test_update_profile,
        test_update_profile_partial,
        test_validation_errors,
        test_search_profiles,
        test_profiles_by_stage
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test(token):
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Profile API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
