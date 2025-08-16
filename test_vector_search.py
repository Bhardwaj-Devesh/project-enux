#!/usr/bin/env python3
"""
Test script for vector search functionality
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

async def test_vector_search():
    """Test the vector search API endpoint"""
    
    # Test queries
    test_queries = [
        "sales strategy",
        "startup growth",
        "marketing tactics",
        "business development"
    ]
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"\n🔍 Testing vector search for: '{query}'")
            
            try:
                # Make the request
                url = f"{base_url}/api/v1/playbooks/search/vector"
                params = {
                    "query": query,
                    "limit": 5
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        results = await response.json()
                        print(f"✅ Success! Found {len(results)} results")
                        
                        for i, result in enumerate(results, 1):
                            playbook = result["playbook"]
                            similarity = result["similarity_score"]
                            print(f"  {i}. {playbook['title']} (similarity: {similarity:.3f})")
                            print(f"     ID: {playbook['id']}")
                            print(f"     Tags: {playbook.get('tags', [])}")
                            print(f"     Stage: {playbook.get('stage', 'N/A')}")
                            print(f"     Summary: {playbook.get('summary', 'N/A')[:100]}...")
                            print()
                    else:
                        error_text = await response.text()
                        print(f"❌ Error {response.status}: {error_text}")
                        
            except Exception as e:
                print(f"❌ Request failed: {e}")

async def test_playbook_status():
    """Test getting playbook processing status"""
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # First get all playbooks to find one with an ID
            url = f"{base_url}/api/v1/playbooks"
            async with session.get(url) as response:
                if response.status == 200:
                    playbooks = await response.json()
                    if playbooks:
                        playbook_id = playbooks[0]["id"]
                        print(f"\n📊 Testing status for playbook: {playbook_id}")
                        
                        # Get status
                        status_url = f"{base_url}/api/v1/playbooks/{playbook_id}/status"
                        async with session.get(status_url) as status_response:
                            if status_response.status == 200:
                                status_data = await status_response.json()
                                print(f"✅ Status: {status_data['status']}")
                                print(f"   Message: {status_data['message']}")
                                print(f"   Has summary: {bool(status_data.get('summary'))}")
                                print(f"   Has vector embedding: {bool(status_data.get('vector_embedding'))}")
                            else:
                                error_text = await status_response.text()
                                print(f"❌ Status check failed: {error_text}")
                    else:
                        print("❌ No playbooks found to test status")
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get playbooks: {error_text}")
                    
        except Exception as e:
            print(f"❌ Status test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting vector search tests...")
    asyncio.run(test_vector_search())
    asyncio.run(test_playbook_status())
    print("\n✅ Tests completed!")
