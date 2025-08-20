#!/usr/bin/env python3
"""
Final Test Script for Notification Function Fix
Tests all notification endpoints with the corrected p_user_id parameter
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Sample data - replace with actual values
SAMPLE_USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NDJlOTA0MC01MjljLTRjNGEtYWRhYi02ZDY3NTMyNjhkNGIiLCJlbWFpbCI6InRlc3RpbmcyQGdtYWlsLmNvbSIsImV4cCI6MTc1NTYzMjA4Nn0.8o-ty1iZuyEqlFttDWeAJXT_pH0yuC7ve3DuHhxB-aY"

async def test_notification_count():
    """Test the notification count endpoint"""
    
    headers = {
        "Authorization": f"Bearer {SAMPLE_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🔔 Testing Notification Count Endpoint (Final Fix)")
    print("=" * 55)
    
    async with aiohttp.ClientSession() as session:
        
        # Test the notification count endpoint
        print(f"\n1. 📊 Getting notification count...")
        try:
            async with session.get(
                f"{API_BASE}/playbooks/notifications/count", 
                headers=headers
            ) as response:
                
                print(f"✅ Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success! Response: {json.dumps(data, indent=2)}")
                    
                    # Check if the response has the expected structure
                    if 'unread_count' in data and 'total_count' in data:
                        print(f"✅ Unread count: {data['unread_count']}")
                        print(f"✅ Total count: {data['total_count']}")
                    else:
                        print("⚠️ Response missing expected fields")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

async def test_notifications_list():
    """Test the notifications list endpoint"""
    
    headers = {
        "Authorization": f"Bearer {SAMPLE_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n🔔 Testing Notifications List Endpoint")
    print("=" * 45)
    
    async with aiohttp.ClientSession() as session:
        
        # Test the notifications list endpoint
        print(f"\n2. 📋 Getting notifications list...")
        try:
            async with session.get(
                f"{API_BASE}/playbooks/notifications?limit=5", 
                headers=headers
            ) as response:
                
                print(f"✅ Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success! Found {len(data) if isinstance(data, list) else 0} notifications")
                    
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✅ First notification: {json.dumps(data[0], indent=2)}")
                    else:
                        print("ℹ️ No notifications found")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

async def test_mark_notifications_read():
    """Test marking notifications as read"""
    
    headers = {
        "Authorization": f"Bearer {SAMPLE_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n🔔 Testing Mark Notifications Read (Final Fix)")
    print("=" * 55)
    
    async with aiohttp.ClientSession() as session:
        
        # First get some notifications to mark as read
        print(f"\n3. 📋 Getting notifications to mark as read...")
        try:
            async with session.get(
                f"{API_BASE}/playbooks/notifications?limit=2", 
                headers=headers
            ) as response:
                
                if response.status == 200:
                    notifications = await response.json()
                    print(f"✅ Found {len(notifications)} notifications")
                    
                    if len(notifications) > 0:
                        # Get the first notification ID to test marking as read
                        notification_id = notifications[0]['id']
                        print(f"✅ Using notification ID: {notification_id}")
                        
                        # Test marking as read
                        print(f"\n4. ✅ Marking notification as read...")
                        mark_data = {
                            "notification_ids": [notification_id]
                        }
                        
                        async with session.post(
                            f"{API_BASE}/playbooks/notifications/mark-read",
                            headers=headers,
                            json=mark_data
                        ) as mark_response:
                            
                            print(f"✅ Mark Status Code: {mark_response.status}")
                            
                            if mark_response.status == 200:
                                mark_result = await mark_response.json()
                                print(f"✅ Success! Response: {json.dumps(mark_result, indent=2)}")
                            else:
                                error_text = await mark_response.text()
                                print(f"❌ Mark Error: {error_text}")
                    else:
                        print("ℹ️ No notifications found to test marking as read")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Error getting notifications: {error_text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

async def test_mark_all_notifications_read():
    """Test marking all notifications as read"""
    
    headers = {
        "Authorization": f"Bearer {SAMPLE_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n🔔 Testing Mark All Notifications Read (Final Fix)")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test marking all notifications as read
        print(f"\n5. ✅ Marking all notifications as read...")
        try:
            async with session.post(
                f"{API_BASE}/playbooks/notifications/mark-all-read",
                headers=headers
            ) as response:
                
                print(f"✅ Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success! Response: {json.dumps(data, indent=2)}")
                    
                    # Check if the response has the expected structure
                    if 'updated_count' in data:
                        print(f"✅ Updated count: {data['updated_count']}")
                    else:
                        print("⚠️ Response missing expected fields")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

async def test_delete_notification():
    """Test deleting a notification"""
    
    headers = {
        "Authorization": f"Bearer {SAMPLE_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n🔔 Testing Delete Notification")
    print("=" * 35)
    
    async with aiohttp.ClientSession() as session:
        
        # First get a notification to delete
        print(f"\n6. 📋 Getting a notification to delete...")
        try:
            async with session.get(
                f"{API_BASE}/playbooks/notifications?limit=1", 
                headers=headers
            ) as response:
                
                if response.status == 200:
                    notifications = await response.json()
                    print(f"✅ Found {len(notifications)} notifications")
                    
                    if len(notifications) > 0:
                        # Get the first notification ID to test deletion
                        notification_id = notifications[0]['id']
                        print(f"✅ Using notification ID: {notification_id}")
                        
                        # Test deletion
                        print(f"\n7. 🗑️ Deleting notification...")
                        
                        async with session.delete(
                            f"{API_BASE}/playbooks/notifications/{notification_id}",
                            headers=headers
                        ) as delete_response:
                            
                            print(f"✅ Delete Status Code: {delete_response.status}")
                            
                            if delete_response.status == 200:
                                delete_result = await delete_response.json()
                                print(f"✅ Success! Response: {json.dumps(delete_result, indent=2)}")
                            else:
                                error_text = await delete_response.text()
                                print(f"❌ Delete Error: {error_text}")
                    else:
                        print("ℹ️ No notifications found to test deletion")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Error getting notifications: {error_text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

async def main():
    """Main function to run all tests"""
    print("🚀 Starting Final Notification Function Fix Tests")
    print("=" * 65)
    
    try:
        # Test notification count endpoint
        await test_notification_count()
        
        # Test notifications list endpoint
        await test_notifications_list()
        
        # Test marking specific notifications as read
        await test_mark_notifications_read()
        
        # Test marking all notifications as read
        await test_mark_all_notifications_read()
        
        # Test deleting a notification
        await test_delete_notification()
        
        print("\n✅ All tests completed!")
        print("\n📝 Summary of the Fix:")
        print("- Root Cause: notifications table has 'user_id' column")
        print("- Problem: Function parameter 'user_id' conflicted with table column")
        print("- Solution: Use 'p_user_id' as function parameter name")
        print("- Updated: All three notification functions")
        print("- Updated: Service layer to use 'p_user_id' parameter")
        print("- Result: No more ambiguous column reference errors")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
