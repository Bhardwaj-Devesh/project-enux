#!/usr/bin/env python3
"""
Simple test script for vector embedding functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai_service import ai_service


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
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding creation failed: {e}")
        return False


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
            "A comprehensive business plan for an AI-powered analytics startup",
            None  # blog_content
        )
        
        print(f"✅ AI processing completed")
        print(f"📝 Summary: {ai_results['summary'][:100]}...")
        print(f"🏷️ Tags: {ai_results['tags']}")
        print(f"📈 Stage: {ai_results['stage']}")
        print(f"🔢 Embedding dimensions: {len(ai_results['embedding'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI processing failed: {e}")
        return False


async def main():
    """Run tests"""
    print("🚀 Starting Simple Vector Embedding Tests")
    print("=" * 50)
    
    # Run tests
    tests = [
        test_embedding_creation,
        test_ai_processing
    ]
    
    results = {}
    for test in tests:
        try:
            result = await test()
            results[test.__name__] = result
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
