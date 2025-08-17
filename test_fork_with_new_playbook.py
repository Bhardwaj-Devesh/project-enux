#!/usr/bin/env python3
"""
Test script for the updated fork functionality that creates a new playbook record.
This script tests the /fork API endpoint with the new implementation.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

async def test_fork_functionality():
    """Test the complete fork functionality"""
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Fork Functionality with New Playbook Creation")
        print("=" * 60)
        
        # Step 1: Login to get authentication token
        print("\n1️⃣ Logging in...")
        login_data = {
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            if response.status != 200:
                print(f"❌ Login failed: {response.status}")
                return
            
            login_result = await response.json()
            token = login_result.get("access_token")
            if not token:
                print("❌ No access token received")
                return
            
            print("✅ Login successful")
        
        # Set up headers for authenticated requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Step 2: Get available playbooks to fork
        print("\n2️⃣ Getting available playbooks...")
        async with session.get(f"{BASE_URL}/playbooks", headers=headers) as response:
            if response.status != 200:
                print(f"❌ Failed to get playbooks: {response.status}")
                return
            
            playbooks = await response.json()
            if not playbooks:
                print("❌ No playbooks available to fork")
                return
            
            # Find a playbook that's not owned by the current user
            target_playbook = None
            for playbook in playbooks:
                if playbook.get("owner_id") != "current_user_id":  # This would need to be the actual user ID
                    target_playbook = playbook
                    break
            
            if not target_playbook:
                print("❌ No suitable playbook found to fork (all owned by current user)")
                return
            
            print(f"✅ Found playbook to fork: {target_playbook['title']} (ID: {target_playbook['id']})")
        
        # Step 3: Fork the playbook
        print("\n3️⃣ Forking playbook...")
        fork_data = {
            "playbook_id": target_playbook['id']
        }
        
        async with session.post(f"{BASE_URL}/playbooks/fork", json=fork_data, headers=headers) as response:
            if response.status != 200:
                print(f"❌ Fork failed: {response.status}")
                error_text = await response.text()
                print(f"Error details: {error_text}")
                return
            
            fork_result = await response.json()
            print("✅ Fork successful!")
            print(f"   New playbook ID: {fork_result.get('new_playbook_id')}")
            print(f"   New playbook URL: {fork_result.get('new_playbook_url')}")
            print(f"   Message: {fork_result.get('message')}")
        
        # Step 4: Verify the new playbook exists
        print("\n4️⃣ Verifying new playbook...")
        new_playbook_id = fork_result.get('new_playbook_id')
        
        async with session.get(f"{BASE_URL}/playbooks/{new_playbook_id}", headers=headers) as response:
            if response.status != 200:
                print(f"❌ Failed to get new playbook: {response.status}")
                return
            
            new_playbook = await response.json()
            print("✅ New playbook retrieved successfully!")
            print(f"   Title: {new_playbook.get('title')}")
            print(f"   Owner ID: {new_playbook.get('owner_id')}")
            print(f"   Version: {new_playbook.get('version')}")
            print(f"   Files count: {len(new_playbook.get('files', {}))}")
        
        # Step 5: Check user's playbooks to see the fork
        print("\n5️⃣ Checking user's playbooks...")
        async with session.get(f"{BASE_URL}/playbooks/my-playbooks", headers=headers) as response:
            if response.status != 200:
                print(f"❌ Failed to get user's playbooks: {response.status}")
                return
            
            user_playbooks = await response.json()
            print(f"✅ User has {len(user_playbooks)} playbooks")
            
            # Check if the new playbook is in the user's list
            new_playbook_found = any(pb.get('id') == new_playbook_id for pb in user_playbooks)
            if new_playbook_found:
                print("✅ New playbook found in user's playbooks list")
            else:
                print("⚠️ New playbook not found in user's playbooks list")
        
        # Step 6: Check fork information
        print("\n6️⃣ Checking fork information...")
        async with session.get(f"{BASE_URL}/playbooks/{target_playbook['id']}/fork-info", headers=headers) as response:
            if response.status != 200:
                print(f"❌ Failed to get fork info: {response.status}")
                return
            
            fork_info = await response.json()
            print("✅ Fork information retrieved!")
            print(f"   Total forks: {fork_info.get('total_forks')}")
            print(f"   Can fork: {fork_info.get('can_fork')}")
            print(f"   User fork: {fork_info.get('user_fork')}")
        
        print("\n🎉 Fork functionality test completed successfully!")
        print("=" * 60)

if __name__ == "__main__":
    print("🚀 Starting Fork Functionality Test")
    print("Make sure the server is running on http://localhost:8000")
    print("Make sure you have a test user and some playbooks in the database")
    
    try:
        asyncio.run(test_fork_functionality())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
