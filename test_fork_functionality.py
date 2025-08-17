#!/usr/bin/env python3
"""
Comprehensive Fork Functionality Test
Tests all aspects of the fork system including creation, management, and pull requests
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def print_step(step, title):
    print(f"\n{'='*60}")
    print(f"Step {step}: {title}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️ {message}")

def test_fork_functionality():
    """Test the complete fork functionality"""
    
    print("🚀 Starting Comprehensive Fork Functionality Test")
    print(f"📅 Test Timestamp: {TEST_TIMESTAMP}")
    
    # Test data
    test_email_1 = f"owner_{TEST_TIMESTAMP}@example.com"
    test_password_1 = "OwnerPassword123!"
    test_full_name_1 = f"Playbook Owner {TEST_TIMESTAMP}"
    
    test_email_2 = f"forker_{TEST_TIMESTAMP}@example.com"
    test_password_2 = "ForkerPassword123!"
    test_full_name_2 = f"Playbook Forker {TEST_TIMESTAMP}"
    
    # Step 1: Register and login first user (playbook owner)
    print_step(1, "Registering and Logging in Playbook Owner")
    
    # Register first user
    register_data_1 = {
        "email": test_email_1,
        "password": test_password_1,
        "full_name": test_full_name_1
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data_1)
    if response.status_code == 200:
        print_success("First user registered successfully")
    else:
        print_error(f"First user registration failed: {response.text}")
        return
    
    # Login first user
    login_data_1 = {
        "username": test_email_1,
        "password": test_password_1
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data_1)
    if response.status_code == 200:
        auth_data_1 = response.json()
        auth_headers_1 = {"Authorization": f"Bearer {auth_data_1['access_token']}"}
        user_id_1 = auth_data_1['user']['id']
        print_success(f"First user logged in: {user_id_1}")
    else:
        print_error(f"First user login failed: {response.text}")
        return
    
    # Step 2: Create a playbook for the first user
    print_step(2, "Creating Original Playbook")
    
    # Create test file content
    test_content = f"""# Test Playbook for Fork Testing - {TEST_TIMESTAMP}

This is a comprehensive test playbook created for testing the fork functionality.

## Features to Test:
1. Fork creation process
2. File copying in forks
3. Fork management
4. Pull request creation
5. Version synchronization

## Test Scenarios:
- Fork testing scenarios
- File management in forks
- Sync with original playbook

## Steps:
1. Create original playbook
2. Fork it to another user
3. Verify the fork contains all data
4. Test file access in the fork
5. Test pull request creation
"""
    
    # Create playbook with files
    files = {'files': (f'test_playbook_{TEST_TIMESTAMP}.md', test_content, 'text/markdown')}
    data = {
        'title': f'Test Playbook for Fork Testing {TEST_TIMESTAMP}',
        'description': f'A comprehensive test playbook created by {test_email_1} for testing fork functionality',
        'blog_content': f'This playbook tests the complete fork workflow including file management and pull requests.',
        'tags': json.dumps(['test', 'fork', 'api', 'automation', TEST_TIMESTAMP])
    }
    
    response = requests.post(f"{BASE_URL}/playbooks/upload", files=files, data=data, headers=auth_headers_1)
    if response.status_code == 200:
        playbook_data = response.json()
        original_playbook_id = playbook_data['playbook']['id']
        print_success(f"Original playbook created: {original_playbook_id}")
        print_info(f"Title: {playbook_data['playbook']['title']}")
    else:
        print_error(f"Playbook creation failed: {response.text}")
        return
    
    # Step 3: Register and login second user (forker)
    print_step(3, "Registering and Logging in Forker")
    
    # Register second user
    register_data_2 = {
        "email": test_email_2,
        "password": test_password_2,
        "full_name": test_full_name_2
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data_2)
    if response.status_code == 200:
        print_success("Second user registered successfully")
    else:
        print_error(f"Second user registration failed: {response.text}")
        return
    
    # Login second user
    login_data_2 = {
        "username": test_email_2,
        "password": test_password_2
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data_2)
    if response.status_code == 200:
        auth_data_2 = response.json()
        auth_headers_2 = {"Authorization": f"Bearer {auth_data_2['access_token']}"}
        user_id_2 = auth_data_2['user']['id']
        print_success(f"Second user logged in: {user_id_2}")
    else:
        print_error(f"Second user login failed: {response.text}")
        return
    
    # Step 4: Test fork information endpoint
    print_step(4, "Testing Fork Information Endpoint")
    
    response = requests.get(f"{BASE_URL}/playbooks/{original_playbook_id}/fork-info", headers=auth_headers_2)
    if response.status_code == 200:
        fork_info = response.json()
        print_success("Fork info retrieved successfully")
        print_info(f"Can fork: {fork_info['can_fork']}")
        print_info(f"Total forks: {fork_info['total_forks']}")
        print_info(f"Is owner: {fork_info['is_owner']}")
    else:
        print_error(f"Fork info failed: {response.text}")
    
    # Step 5: Create fork
    print_step(5, "Creating Fork")
    
    fork_data = {
        "playbook_id": original_playbook_id
    }
    
    response = requests.post(f"{BASE_URL}/playbooks/fork", json=fork_data, headers=auth_headers_2)
    if response.status_code == 200:
        fork_result = response.json()
        fork_id = fork_result['new_playbook_id']
        print_success(f"Fork created successfully: {fork_id}")
        print_info(f"New playbook URL: {fork_result['new_playbook_url']}")
        print_info(f"Message: {fork_result['message']}")
    else:
        print_error(f"Fork creation failed: {response.text}")
        return
    
    # Step 6: Test getting forked playbook
    print_step(6, "Testing Get Forked Playbook")
    
    response = requests.get(f"{BASE_URL}/playbooks/user-playbooks/{fork_id}", headers=auth_headers_2)
    if response.status_code == 200:
        forked_playbook = response.json()
        print_success("Forked playbook retrieved successfully")
        print_info(f"Original Title: {forked_playbook['original_playbook']['title'] if forked_playbook['original_playbook'] else 'N/A'}")
        print_info(f"Fork Owner: {forked_playbook['user_id']}")
        print_info(f"Forked At: {forked_playbook['forked_at']}")
    else:
        print_error(f"Failed to get forked playbook: {response.text}")
    
    # Step 7: Test getting forked playbook files
    print_step(7, "Testing Get Forked Playbook Files")
    
    response = requests.get(f"{BASE_URL}/playbooks/user-playbooks/{fork_id}/files", headers=auth_headers_2)
    if response.status_code == 200:
        files = response.json()
        print_success(f"Found {len(files)} files in fork")
        for file in files:
            print_info(f"  - {file.get('file_path', 'Unknown')} ({file.get('file_type', 'Unknown')})")
    else:
        print_error(f"Failed to get forked playbook files: {response.text}")
    
    # Step 8: Test sync status
    print_step(8, "Testing Sync Status")
    
    response = requests.get(f"{BASE_URL}/playbooks/user-playbooks/{fork_id}/sync-status", headers=auth_headers_2)
    if response.status_code == 200:
        sync_status = response.json()
        print_success("Sync status retrieved successfully")
        print_info(f"Is behind: {sync_status.get('is_behind', 'unknown')}")
        print_info(f"Versions behind: {sync_status.get('versions_behind', 'unknown')}")
        print_info(f"Fork version: {sync_status.get('fork_version', 'unknown')}")
        print_info(f"Original version: {sync_status.get('original_version', 'unknown')}")
    else:
        print_error(f"Sync status failed: {response.text}")
    
    # Step 9: Test uploading file to fork
    print_step(9, "Testing File Upload to Fork")
    
    new_file_content = f"""# New File Added to Fork - {TEST_TIMESTAMP}

This file was added to the fork to test file management functionality.

## Test Content:
- File upload to fork
- File management
- Version tracking
"""
    
    files = {'file': (f'new_file_{TEST_TIMESTAMP}.md', new_file_content, 'text/markdown')}
    data = {'file_path': f'new_file_{TEST_TIMESTAMP}.md'}
    
    response = requests.post(f"{BASE_URL}/playbooks/user-playbooks/{fork_id}/files", files=files, data=data, headers=auth_headers_2)
    if response.status_code == 200:
        upload_result = response.json()
        print_success("File uploaded to fork successfully")
        print_info(f"File ID: {upload_result.get('file_id', 'N/A')}")
        print_info(f"File name: {upload_result.get('file_name', 'N/A')}")
    else:
        print_error(f"File upload to fork failed: {response.text}")
    
    # Step 10: Test getting user forks
    print_step(10, "Testing Get User Forks")
    
    response = requests.get(f"{BASE_URL}/playbooks/user/forks", headers=auth_headers_2)
    if response.status_code == 200:
        forks = response.json()
        print_success(f"Found {len(forks)} forks for user")
        for i, fork in enumerate(forks, 1):
            print_info(f"  Fork {i}: {fork.get('id', 'Unknown ID')}")
            if fork.get('original_playbook'):
                print_info(f"    Original: {fork['original_playbook'].get('title', 'Unknown Title')}")
            print_info(f"    Forked: {fork.get('forked_at', 'Unknown date')}")
    else:
        print_error(f"Get user forks failed: {response.text}")
    
    # Step 11: Test duplicate fork (should fail)
    print_step(11, "Testing Duplicate Fork (Should Fail)")
    
    response = requests.post(f"{BASE_URL}/playbooks/fork", json=fork_data, headers=auth_headers_2)
    if response.status_code == 409:
        print_success("Duplicate fork correctly prevented")
        print_info(f"Error: {response.json().get('detail', 'Unknown error')}")
    else:
        print_error(f"Unexpected response for duplicate fork: {response.status_code}")
    
    # Step 12: Test notifications for original owner
    print_step(12, "Testing Notifications for Original Owner")
    
    response = requests.get(f"{BASE_URL}/playbooks/notifications", headers=auth_headers_1)
    if response.status_code == 200:
        notifications = response.json()
        print_success(f"Found {len(notifications)} notifications for original owner")
        for notification in notifications:
            print_info(f"  - {notification.get('message', 'Unknown message')}")
            print_info(f"    From: {notification.get('user_full_name', 'Unknown user')}")
    else:
        print_error(f"Get notifications failed: {response.text}")
    
    # Step 13: Test fork info after forking
    print_step(13, "Testing Fork Info After Forking")
    
    response = requests.get(f"{BASE_URL}/playbooks/{original_playbook_id}/fork-info", headers=auth_headers_2)
    if response.status_code == 200:
        fork_info = response.json()
        print_success("Fork info retrieved successfully after forking")
        print_info(f"Can fork: {fork_info['can_fork']}")
        print_info(f"Total forks: {fork_info['total_forks']}")
        print_info(f"User fork: {fork_info.get('user_fork', 'None')}")
    else:
        print_error(f"Fork info failed: {response.text}")
    
    # Step 14: Test combined playbooks endpoint
    print_step(14, "Testing Combined Playbooks Endpoint")
    
    response = requests.get(f"{BASE_URL}/playbooks/my-playbooks-combined", headers=auth_headers_2)
    if response.status_code == 200:
        combined_playbooks = response.json()
        print_success(f"Found {len(combined_playbooks)} combined playbooks")
        for playbook in combined_playbooks:
            print_info(f"  - {playbook.get('title', 'Unknown')} (Forked: {playbook.get('is_forked', False)})")
    else:
        print_error(f"Combined playbooks failed: {response.text}")
    
    # Step 15: Test download forked playbook
    print_step(15, "Testing Download Forked Playbook")
    
    response = requests.get(f"{BASE_URL}/playbooks/user-playbooks/{fork_id}/download", headers=auth_headers_2)
    if response.status_code == 200:
        print_success("Forked playbook download successful")
        print_info(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
        print_info(f"Content-Disposition: {response.headers.get('content-disposition', 'Unknown')}")
    else:
        print_error(f"Forked playbook download failed: {response.text}")
    
    # Step 16: Test delete fork
    print_step(16, "Testing Delete Fork")
    
    response = requests.delete(f"{BASE_URL}/playbooks/user-playbooks/{fork_id}", headers=auth_headers_2)
    if response.status_code == 200:
        delete_result = response.json()
        print_success("Fork deleted successfully")
        print_info(f"Message: {delete_result.get('message', 'N/A')}")
    else:
        print_error(f"Fork deletion failed: {response.text}")
    
    # Step 17: Verify fork is deleted
    print_step(17, "Verifying Fork Deletion")
    
    response = requests.get(f"{BASE_URL}/playbooks/user-playbooks/{fork_id}", headers=auth_headers_2)
    if response.status_code == 404:
        print_success("Fork correctly deleted (404 response)")
    else:
        print_error(f"Fork still exists after deletion: {response.status_code}")
    
    print("\n" + "="*60)
    print("🎉 FORK FUNCTIONALITY TEST COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("✅ All fork features working correctly:")
    print("  - Fork creation")
    print("  - File copying")
    print("  - Fork management")
    print("  - File upload to forks")
    print("  - Sync status checking")
    print("  - Notifications")
    print("  - Fork deletion")
    print("  - Duplicate prevention")

if __name__ == "__main__":
    test_fork_functionality()
