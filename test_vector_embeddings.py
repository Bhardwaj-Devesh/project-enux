#!/usr/bin/env python3
"""
Test script for vector embedding functionality
This script tests the complete vector embedding pipeline
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.services.supabase_service import supabase_service
from app.config import settings


async def test_embedding_creation():
    """Test embedding creation functionality"""
    print("🧪 Testing embedding creation...")
    
    # Test text
    test_text = "This is a test playbook about business strategy and growth"
    
    try:
        # Create embedding
        embedding = await ai_service.create_embedding(test_text)
        
        print(f"✅ Embedding created successfully")
        print(f"📊 Embedding dimensions: {len(embedding)}")
        print(f"🔢 First 5 values: {embedding[:5]}")
        print(f"📈 Embedding norm: {sum(x*x for x in embedding)**0.5:.4f}")
        
        return embedding
        
    except Exception as e:
        print(f"❌ Embedding creation failed: {e}")
        return None


async def test_vector_storage():
    """Test vector storage functionality"""
    print("\n🧪 Testing vector storage...")
    
    # Create test file data
    test_files = [
        {
            "filename": "test_strategy.md",
            "content": "# Business Strategy\n\nThis is a comprehensive business strategy document covering market analysis, competitive positioning, and growth plans.",
            "content_type": "text/markdown"
        },
        {
            "filename": "test_operations.txt",
            "content": "Operations Manual\n\nThis document outlines operational procedures, team structure, and process workflows for efficient business operations.",
            "content_type": "text/plain"
        }
    ]
    
    try:
        # Store vectors
        result = await vector_service.store_file_vectors(test_files, "test-playbook-id")
        
        print(f"✅ Vector storage result: {result['success']}")
        print(f"📊 Stored vectors: {result['stored_count']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Vector storage failed: {e}")
        return None


async def test_vector_search():
    """Test vector search functionality"""
    print("\n🧪 Testing vector search...")
    
    query = "business strategy and growth"
    
    try:
        # Search for similar files
        results = await vector_service.search_similar_files(query, limit=5)
        
        print(f"✅ Vector search completed")
        print(f"📊 Found {len(results)} results")
        
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. {result.get('filename', 'Unknown')} (similarity: {result.get('similarity', 0):.3f})")
        
        return results
        
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return None


async def test_playbook_vector_search():
    """Test playbook vector search functionality"""
    print("\n🧪 Testing playbook vector search...")
    
    query = "business strategy"
    
    try:
        # Create query embedding
        query_embedding = await ai_service.create_embedding(query)
        
        # Search playbooks
        results = await supabase_service.search_playbooks_vector(query_embedding, limit=5)
        
        print(f"✅ Playbook vector search completed")
        print(f"📊 Found {len(results)} results")
        
        for i, result in enumerate(results[:3]):
            playbook = result.get('playbook', {})
            similarity = result.get('similarity', 0)
            print(f"  {i+1}. {playbook.get('title', 'Unknown')} (similarity: {similarity:.3f})")
        
        return results
        
    except Exception as e:
        print(f"❌ Playbook vector search failed: {e}")
        return None


async def test_ai_processing():
    """Test complete AI processing pipeline"""
    print("\n🧪 Testing AI processing pipeline...")
    
    # Test files
    test_files = [
        {
            "filename": "business_plan.md",
            "content": """# Business Plan

## Executive Summary
This is a comprehensive business plan for a SaaS startup focused on AI-powered analytics.

## Market Analysis
The market for AI analytics is growing rapidly, with increasing demand for data-driven insights.

## Strategy
Our strategy focuses on product-led growth, customer success, and continuous innovation.

## Financial Projections
We project $10M ARR within 3 years with strong unit economics.
""",
            "content_type": "text/markdown"
        }
    ]
    
    try:
        # Process with AI
        ai_results = await ai_service.process_playbook_files(
            test_files,
            "AI Analytics Business Plan",
            "A comprehensive business plan for an AI-powered analytics startup"
        )
        
        print(f"✅ AI processing completed")
        print(f"📝 Summary: {ai_results['summary'][:100]}...")
        print(f"🏷️ Tags: {ai_results['tags']}")
        print(f"📈 Stage: {ai_results['stage']}")
        print(f"🔢 Embedding dimensions: {len(ai_results['embedding'])}")
        
        return ai_results
        
    except Exception as e:
        print(f"❌ AI processing failed: {e}")
        return None


async def test_database_connection():
    """Test database connection and basic operations"""
    print("\n🧪 Testing database connection...")
    
    try:
        # Test basic query
        result = await supabase_service.client.table("playbooks").select("id").limit(1).execute()
        
        print(f"✅ Database connection successful")
        print(f"📊 Playbooks table accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting Vector Embedding Tests")
    print("=" * 50)
    
    # Test database connection first
    db_ok = await test_database_connection()
    if not db_ok:
        print("❌ Database connection failed, stopping tests")
        return
    
    # Run tests
    tests = [
        test_embedding_creation,
        test_vector_storage,
        test_vector_search,
        test_playbook_vector_search,
        test_ai_processing
    ]
    
    results = {}
    for test in tests:
        try:
            result = await test()
            results[test.__name__] = result is not None
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results[test.__name__] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vector embeddings are working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
