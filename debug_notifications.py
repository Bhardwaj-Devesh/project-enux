#!/usr/bin/env python3
"""
Debug script to test notifications functionality
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.supabase_service import supabase_service

async def debug_notifications():
    """Debug the notifications functionality"""
    
    # Test user ID (replace with actual user ID)
    test_user_id = "642e9040-529c-4c4a-adab-6d6753268d4b"
    
    print("🔍 Debugging Notifications...")
    print(f"Test User ID: {test_user_id}")
    
    try:
        # 1. Check if user exists
        print("\n1. Checking if user exists...")
        user = await supabase_service.get_user_by_id(test_user_id)
        if user:
            print(f"✅ User found: {user.get('email')}")
        else:
            print("❌ User not found")
            return
        
        # 2. Get owned playbooks
        print("\n2. Getting owned playbooks...")
        owned_playbooks = await supabase_service.get_playbooks_by_user_detailed(test_user_id, 10, 0)
        print(f"✅ Found {len(owned_playbooks)} owned playbooks")
        
        if not owned_playbooks:
            print("❌ No owned playbooks found")
            return
        
        # 3. Get playbook IDs
        playbook_ids = [p['id'] for p in owned_playbooks]
        print(f"Playbook IDs: {playbook_ids}")
        
        # 4. Check for forks of these playbooks
        print("\n3. Checking for forks...")
        for playbook_id in playbook_ids:
            fork_count = await supabase_service.get_playbook_fork_count(playbook_id)
            print(f"Playbook {playbook_id}: {fork_count} forks")
        
        # 5. Test the notifications query directly
        print("\n4. Testing notifications query...")
        response = supabase_service.client.table("user_playbooks").select("""
            *,
            users!user_playbooks_user_id_fkey (
                id, email, full_name
            ),
            playbooks!user_playbooks_original_playbook_id_fkey (
                id, title
            )
        """).in_("original_playbook_id", playbook_ids).limit(5).execute()
        
        print(f"✅ Raw query returned {len(response.data)} results")
        
        # 6. Analyze the data structure
        print("\n5. Analyzing data structure...")
        for i, fork in enumerate(response.data):
            print(f"\nFork {i+1}:")
            print(f"  - Fork ID: {fork.get('id')}")
            print(f"  - Original Playbook ID: {fork.get('original_playbook_id')}")
            print(f"  - User ID: {fork.get('user_id')}")
            print(f"  - Forked At: {fork.get('forked_at')}")
            
            user_info = fork.get('users', {})
            print(f"  - User Info: {user_info}")
            
            playbook_info = fork.get('playbooks', {})
            print(f"  - Playbook Info: {playbook_info}")
        
        # 7. Test the notifications method
        print("\n6. Testing get_user_notifications method...")
        notifications = await supabase_service.get_user_notifications(test_user_id, 10, 0)
        print(f"✅ Notifications method returned {len(notifications)} notifications")
        
        for i, notification in enumerate(notifications):
            print(f"\nNotification {i+1}:")
            print(f"  - Type: {notification.get('type')}")
            print(f"  - Message: {notification.get('message')}")
            print(f"  - Playbook ID: {notification.get('playbook_id')}")
            print(f"  - User ID: {notification.get('user_id')}")
            print(f"  - User Email: {notification.get('user_email')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_notifications())
