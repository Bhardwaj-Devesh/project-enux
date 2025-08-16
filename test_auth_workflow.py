#!/usr/bin/env python3
"""
Test script to verify JWT authentication workflow
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_auth_workflow():
    """Test the complete authentication workflow"""
    
    print("Testing JWT Authentication Workflow")
    print("=" * 50)
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    # Step 1: Register a new user
    print("\n1. Testing user registration...")
    try:
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code == 200:
            register_data = register_response.json()
            print("✅ Registration successful!")
            print(f"   User ID: {register_data['user']['id']}")
            print(f"   Email: {register_data['user']['email']}")
            print(f"   Token: {register_data['access_token'][:50]}...")
            
            # Store the token for later use
            auth_token = register_data['access_token']
        else:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"   Response: {register_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return
    
    # Step 2: Test login with JSON
    print("\n2. Testing login with JSON...")
    try:
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        login_response = requests.post(
            f"{BASE_URL}/auth/login-json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print("✅ Login successful!")
            print(f"   Token: {login_data['access_token'][:50]}...")
            print(f"   Expires in: {login_data['expires_in']} seconds")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
    
    # Step 3: Test protected endpoint with token
    print("\n3. Testing protected endpoint...")
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        me_response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=headers
        )
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print("✅ Protected endpoint access successful!")
            print(f"   User ID: {me_data['id']}")
            print(f"   Email: {me_data['email']}")
            print(f"   Full Name: {me_data['full_name']}")
        else:
            print(f"❌ Protected endpoint access failed: {me_response.status_code}")
            print(f"   Response: {me_response.text}")
            
    except Exception as e:
        print(f"❌ Protected endpoint error: {str(e)}")
    
    # Step 4: Test playbooks endpoint with authentication
    print("\n4. Testing playbooks endpoint with authentication...")
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        playbooks_response = requests.get(
            f"{BASE_URL}/playbooks/",
            headers=headers
        )
        
        if playbooks_response.status_code == 200:
            playbooks_data = playbooks_response.json()
            print("✅ Playbooks endpoint access successful!")
            print(f"   Found {len(playbooks_data)} playbooks")
        else:
            print(f"❌ Playbooks endpoint access failed: {playbooks_response.status_code}")
            print(f"   Response: {playbooks_response.text}")
            
    except Exception as e:
        print(f"❌ Playbooks endpoint error: {str(e)}")
    
    # Step 5: Test invalid token
    print("\n5. Testing invalid token...")
    try:
        headers = {
            "Authorization": "Bearer invalid_token_here",
            "Content-Type": "application/json"
        }
        
        invalid_response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=headers
        )
        
        if invalid_response.status_code == 401:
            print("✅ Invalid token correctly rejected!")
        else:
            print(f"❌ Invalid token not rejected: {invalid_response.status_code}")
            
    except Exception as e:
        print(f"❌ Invalid token test error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Authentication workflow test completed!")

if __name__ == "__main__":
    test_auth_workflow()

