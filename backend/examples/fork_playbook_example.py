"""
Example script demonstrating how to fork a playbook using the new fork API endpoints.

This script shows:
1. How to fork an existing playbook
2. How to list user's forked playbooks
3. How to get details of a specific forked playbook

Make sure to:
- Have the FastAPI server running
- Have valid user_id and playbook_id values
- Update the base_url if your server runs on a different port
"""

import requests
import json
from typing import Dict, Any, Optional


class PlaybookForkClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
    
    def fork_playbook(self, playbook_id: str, user_id: str) -> Dict[str, Any]:
        """Fork a playbook to user's workspace"""
        url = f"{self.base_url}/playbooks/fork"
        payload = {
            "playbook_id": playbook_id,
            "user_id": user_id
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Fork failed: {response.status_code} - {response.text}")
    
    def get_user_forks(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get all forked playbooks for a user"""
        url = f"{self.base_url}/playbooks/user/{user_id}/forks"
        params = {"limit": limit, "offset": offset}
        
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Get forks failed: {response.status_code} - {response.text}")
    
    def get_user_playbook(self, user_playbook_id: str) -> Dict[str, Any]:
        """Get details of a specific forked playbook"""
        url = f"{self.base_url}/playbooks/user-playbooks/{user_playbook_id}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Get user playbook failed: {response.status_code} - {response.text}")
    
    def get_user_playbook_files(self, user_playbook_id: str) -> Dict[str, Any]:
        """Get all files associated with a user playbook"""
        url = f"{self.base_url}/playbooks/user-playbooks/{user_playbook_id}/files"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Get user playbook files failed: {response.status_code} - {response.text}")
    
    def list_available_playbooks(self, limit: int = 10) -> Dict[str, Any]:
        """List available playbooks that can be forked"""
        url = f"{self.base_url}/playbooks"
        params = {"limit": limit}
        
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"List playbooks failed: {response.status_code} - {response.text}")


def main():
    """Main example function"""
    client = PlaybookForkClient()
    
    # Example user and playbook IDs (replace with real ones)
    # You can get these by calling the list endpoints first
    sample_user_id = "demo_user_123"  # Replace with actual user ID
    sample_playbook_id = None  # We'll get this from the list
    
    try:
        print("=== Fork Playbook Example ===\n")
        
        # Step 1: List available playbooks to find one to fork
        print("1. Listing available playbooks...")
        playbooks = client.list_available_playbooks(limit=5)
        
        if playbooks:
            print(f"Found {len(playbooks)} playbooks:")
            for i, playbook in enumerate(playbooks, 1):
                print(f"   {i}. {playbook['title']} (ID: {playbook['id']})")
            
            # Use the first playbook as example
            sample_playbook_id = playbooks[0]['id']
            print(f"\nUsing playbook: {playbooks[0]['title']}")
        else:
            print("No playbooks found. Please upload a playbook first.")
            return
        
        # Step 2: Fork the playbook
        print(f"\n2. Forking playbook {sample_playbook_id} for user {sample_user_id}...")
        fork_result = client.fork_playbook(sample_playbook_id, sample_user_id)
        
        print("Fork successful!")
        print(f"   Status: {fork_result['status']}")
        print(f"   New Playbook ID: {fork_result['new_playbook_id']}")
        print(f"   New Playbook URL: {fork_result['new_playbook_url']}")
        print(f"   Message: {fork_result.get('message', 'N/A')}")
        
        new_playbook_id = fork_result['new_playbook_id']
        
        # Step 3: List user's forked playbooks
        print(f"\n3. Listing all forks for user {sample_user_id}...")
        user_forks = client.get_user_forks(sample_user_id)
        
        print(f"User has {len(user_forks)} forked playbooks:")
        for i, fork in enumerate(user_forks, 1):
            original = fork.get('original_playbook')
            original_title = original['title'] if original else 'Unknown'
            print(f"   {i}. Fork of '{original_title}' (ID: {fork['id']})")
            print(f"      Forked at: {fork['forked_at']}")
            print(f"      Status: {fork['status']}")
        
        # Step 4: Get details of the newly created fork
        print(f"\n4. Getting details of the new fork {new_playbook_id}...")
        fork_details = client.get_user_playbook(new_playbook_id)
        
        print("Fork details:")
        print(f"   Fork ID: {fork_details['id']}")
        print(f"   User ID: {fork_details['user_id']}")
        print(f"   Original Playbook ID: {fork_details['original_playbook_id']}")
        print(f"   Version: {fork_details['version']}")
        print(f"   Status: {fork_details['status']}")
        
        if fork_details.get('original_playbook'):
            orig = fork_details['original_playbook']
            print(f"   Original Title: {orig['title']}")
            print(f"   Original Description: {orig['description']}")
        
        # Step 5: Get files associated with the forked playbook
        print(f"\n5. Getting files for the forked playbook {new_playbook_id}...")
        try:
            fork_files = client.get_user_playbook_files(new_playbook_id)
            
            if fork_files:
                print(f"Fork has {len(fork_files)} files:")
                for i, file_info in enumerate(fork_files, 1):
                    print(f"   {i}. {file_info['file_path']} ({file_info['file_type']})")
                    print(f"      Storage: {file_info['storage_path']}")
                    print(f"      Uploaded: {file_info['uploaded_at']}")
            else:
                print("No files found in the forked playbook.")
        except Exception as file_error:
            print(f"   Could not retrieve files: {str(file_error)}")
        
        print("\n=== Example completed successfully! ===")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure the FastAPI server is running on http://localhost:8000")
        print("2. Ensure you have at least one playbook uploaded")
        print("3. Verify the user_id exists in your database")
        print("4. Check that the playbook_id is valid and not already forked by this user")


if __name__ == "__main__":
    main()
