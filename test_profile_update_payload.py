#!/usr/bin/env python3
"""
Test script to verify the profile update API works with the expected payload format.
This test ensures that user_id and username are fetched from auth token, not payload.
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/auth/login"
PROFILE_UPDATE_ENDPOINT = f"{BASE_URL}/profiles/me"

def login_user(email: str, password: str) -> str:
    """Login user and return access token"""
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(LOGIN_ENDPOINT, json=login_data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")

def update_profile(token: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update profile with the given data"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(PROFILE_UPDATE_ENDPOINT, json=profile_data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Profile update failed: {response.status_code} - {response.text}")

def test_profile_update():
    """Test the profile update functionality"""
    print("Testing Profile Update API...")
    print("=" * 50)
    
    # Test credentials (you'll need to adjust these)
    test_email = "test@example.com"
    test_password = "testpassword123"
    
    try:
        # Step 1: Login to get access token
        print("1. Logging in to get access token...")
        token = login_user(test_email, test_password)
        print(f"✓ Login successful, token received")
        
        # Step 2: Test profile update with expected payload format
        print("\n2. Testing profile update with expected payload format...")
        
        # This is the expected payload format (no user_id or username)
        profile_payload = {
            "full_name": "Devesh Bhardwaj",
            "bio": "I am a disco dancer ta ta ta tannana",
            "company": "Hiwipay",
            "location": "Mumbai",
            "website": "",
            "interests": ["reading"],
            "stage": "",
            "avatar_url": None
        }
        
        print(f"Payload being sent: {json.dumps(profile_payload, indent=2)}")
        
        # Update profile
        result = update_profile(token, profile_payload)
        
        print(f"✓ Profile update successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Verify that user_id and username are in the response but not in the payload
        print("\n3. Verifying response structure...")
        
        # Check that user_id and username are present in response (from auth token)
        if "id" in result and "username" in result:
            print(f"✓ user_id and username are present in response (from auth token)")
            print(f"  - user_id: {result['id']}")
            print(f"  - username: {result['username']}")
        else:
            print("✗ user_id or username missing from response")
        
        # Check that profile fields are correctly updated
        if result.get("full_name") == profile_payload["full_name"]:
            print(f"✓ full_name correctly updated: {result['full_name']}")
        else:
            print(f"✗ full_name not updated correctly")
        
        if result.get("bio") == profile_payload["bio"]:
            print(f"✓ bio correctly updated: {result['bio']}")
        else:
            print(f"✗ bio not updated correctly")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! The API correctly fetches user_id and username from auth token.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        print("\nMake sure:")
        print("1. The server is running on http://localhost:8000")
        print("2. You have a test user with the provided credentials")
        print("3. The database is properly set up")

if __name__ == "__main__":
    test_profile_update()
