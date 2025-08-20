#!/usr/bin/env python3
"""
Test script to verify the notification function parameter fix
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
    
    print("🔔 Testing Notification Count Endpoint (Fixed)")
    print("=" * 50)
    
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

async def test_mark_notifications_read():
    """Test marking notifications as read"""
    
    headers = {
        "Authorization": f"Bearer {SAMPLE_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n🔔 Testing Mark Notifications Read (Fixed)")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # First get some notifications to mark as read
        print(f"\n1. 📋 Getting notifications to mark as read...")
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
                        print(f"\n2. ✅ Marking notification as read...")
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
    
    print("\n🔔 Testing Mark All Notifications Read (Fixed)")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test marking all notifications as read
        print(f"\n1. ✅ Marking all notifications as read...")
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

async def main():
    """Main function to run tests"""
    print("🚀 Starting Notification Function Fix Tests")
    print("=" * 60)
    
    try:
        # Test notification count endpoint
        await test_notification_count()
        
        # Test marking specific notifications as read
        await test_mark_notifications_read()
        
        # Test marking all notifications as read
        await test_mark_all_notifications_read()
        
        print("\n✅ All tests completed!")
        print("\n📝 Summary:")
        print("- Fixed parameter names from 'p_user_id' to 'user_id'")
        print("- Updated all three notification functions")
        print("- Service layer now matches database function signatures")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
