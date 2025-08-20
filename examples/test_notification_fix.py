#!/usr/bin/env python3
"""
Test script to verify the notification count fix works correctly
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Sample data - replace with actual values
SAMPLE_USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NDJlOTA0MC01MjljLTRjNGEtYWRhYi02ZDY3NTMyNjhkNGIiLCJlbWFpbCI6InRlc3RpbmcyQGdtYWlsLmNvbSIsImV4cCI6MTc1NTYzMjA4Nn0.8o-ty1iZuyEqlFttDWeAJXT_pH0yuC7ve3DuHhxB-aY"

async def test_notification_count():
    """Test the notification count endpoint"""
    
    headers = {
        "Authorization": f"Bearer {SAMPLE_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🔔 Testing Notification Count Endpoint")
    print("=" * 40)
    
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
    print("=" * 40)
    
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

async def main():
    """Main function to run tests"""
    print("🚀 Starting Notification Fix Tests")
    print("=" * 50)
    
    try:
        # Test notification count endpoint
        await test_notification_count()
        
        # Test notifications list endpoint
        await test_notifications_list()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
