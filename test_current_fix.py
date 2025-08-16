#!/usr/bin/env python3
"""
Quick test to verify the vector search fix
"""

import asyncio
import aiohttp
import json

async def test_vector_search_fix():
    """Test if the vector search works with the current fix"""
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Testing vector search with current fix...")
        
        try:
            url = f"{base_url}/api/v1/playbooks/search/vector"
            params = {
                "query": "sales strategy",
                "limit": 5
            }
            
            async with session.get(url, params=params) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    results = await response.json()
                    print(f"✅ Success! Found {len(results)} results")
                    
                    if results:
                        first_result = results[0]
                        playbook = first_result["playbook"]
                        similarity = first_result["similarity_score"]
                        
                        print(f"🎯 First result:")
                        print(f"   Title: {playbook['title']}")
                        print(f"   ID: {playbook['id']}")
                        print(f"   Similarity: {similarity:.3f}")
                        print(f"   Has created_at: {bool(playbook.get('created_at'))}")
                        print(f"   Has updated_at: {bool(playbook.get('updated_at'))}")
                        print(f"   Has summary: {bool(playbook.get('summary'))}")
                        print(f"   Has tags: {bool(playbook.get('tags'))}")
                        
                        return True
                    else:
                        print("⚠️ No results found (this might be normal if no playbooks exist)")
                        return True
                else:
                    error_text = await response.text()
                    print(f"❌ Error {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Testing vector search fix...")
    success = asyncio.run(test_vector_search_fix())
    
    if success:
        print("\n✅ Vector search fix appears to be working!")
        print("📝 If you still see issues, please run the SQL script in Supabase:")
        print("   - Go to Supabase Dashboard > SQL Editor")
        print("   - Run the SQL from FIX_VECTOR_SEARCH.md")
    else:
        print("\n❌ Vector search still has issues")
        print("📝 Please check the error message and run the SQL script in Supabase")
