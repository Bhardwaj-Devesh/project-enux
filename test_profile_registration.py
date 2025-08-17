#!/usr/bin/env python3
"""
Test script for Profile creation during user registration
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test_profile@example.com"
TEST_PASSWORD = "testpassword123"

def test_registration_with_profile_creation():
    """Test that profile is created during user registration"""
    print("🚀 Testing Profile Creation During Registration...")
    print("=" * 60)
    
    # Test registration
    print("\n📝 Testing user registration...")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Test Profile User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            user_data = token_data.get("user")
            
            print(f"✅ Registration successful")
            print(f"   User ID: {user_data.get('id')}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   Full Name: {user_data.get('full_name')}")
            
            # Test that profile was created
            print("\n🔍 Testing profile creation...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            profile_response = requests.get(f"{BASE_URL}/profiles/me", headers=headers)
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print(f"✅ Profile created successfully during registration")
                print(f"   Profile ID: {profile.get('id')}")
                print(f"   Username: {profile.get('username')}")
                print(f"   Full Name: {profile.get('full_name')}")
                print(f"   Created At: {profile.get('created_at')}")
                
                # Verify username is extracted from email
                expected_username = TEST_EMAIL.split('@')[0]
                if profile.get('username') == expected_username:
                    print(f"✅ Username correctly extracted from email: {expected_username}")
                else:
                    print(f"❌ Username mismatch. Expected: {expected_username}, Got: {profile.get('username')}")
                
                return True
            else:
                print(f"❌ Profile not found after registration: {profile_response.status_code} - {profile_response.text}")
                return False
                
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️  User already exists, testing login instead...")
            
            # Try to login with existing user
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                access_token = token_data.get("access_token")
                
                print(f"✅ Login successful")
                
                # Test profile retrieval
                headers = {"Authorization": f"Bearer {access_token}"}
                profile_response = requests.get(f"{BASE_URL}/profiles/me", headers=headers)
                
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    print(f"✅ Profile exists for existing user")
                    print(f"   Profile ID: {profile.get('id')}")
                    print(f"   Username: {profile.get('username')}")
                    print(f"   Full Name: {profile.get('full_name')}")
                    return True
                else:
                    print(f"❌ Profile not found for existing user: {profile_response.status_code}")
                    return False
            else:
                print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
                return False
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during registration test: {e}")
        return False

def test_multiple_registrations():
    """Test multiple user registrations to ensure unique usernames"""
    print("\n👥 Testing multiple user registrations...")
    
    test_users = [
        {"email": "user1@example.com", "password": "password123", "full_name": "User One"},
        {"email": "user2@example.com", "password": "password123", "full_name": "User Two"},
        {"email": "user3@example.com", "password": "password123", "full_name": "User Three"}
    ]
    
    created_profiles = []
    
    for i, user_data in enumerate(test_users, 1):
        print(f"\n📝 Registering user {i}: {user_data['email']}")
        
        try:
            response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                
                # Get profile
                headers = {"Authorization": f"Bearer {access_token}"}
                profile_response = requests.get(f"{BASE_URL}/profiles/me", headers=headers)
                
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    created_profiles.append(profile)
                    print(f"✅ User {i} profile created: {profile.get('username')}")
                else:
                    print(f"❌ Failed to get profile for user {i}")
                    
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"ℹ️  User {i} already exists")
                
                # Try login
                login_response = requests.post(f"{BASE_URL}/auth/login", json=user_data)
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    access_token = token_data.get("access_token")
                    
                    headers = {"Authorization": f"Bearer {access_token}"}
                    profile_response = requests.get(f"{BASE_URL}/profiles/me", headers=headers)
                    
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        created_profiles.append(profile)
                        print(f"✅ User {i} profile retrieved: {profile.get('username')}")
                    else:
                        print(f"❌ Failed to get profile for existing user {i}")
                else:
                    print(f"❌ Login failed for user {i}")
            else:
                print(f"❌ Registration failed for user {i}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error registering user {i}: {e}")
    
    # Check for unique usernames
    usernames = [profile.get('username') for profile in created_profiles]
    unique_usernames = set(usernames)
    
    print(f"\n📊 Profile Creation Summary:")
    print(f"   Total profiles: {len(created_profiles)}")
    print(f"   Unique usernames: {len(unique_usernames)}")
    print(f"   Usernames: {list(unique_usernames)}")
    
    if len(usernames) == len(unique_usernames):
        print("✅ All usernames are unique")
        return True
    else:
        print("❌ Duplicate usernames found")
        return False

def main():
    """Run all profile registration tests"""
    print("🚀 Starting Profile Registration Tests...")
    print("=" * 60)
    
    # Test single registration
    test1_success = test_registration_with_profile_creation()
    
    # Test multiple registrations
    test2_success = test_multiple_registrations()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Registration with profile creation: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"   Multiple user registrations: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! Profile creation during registration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
