#!/usr/bin/env python3
"""
Vector Database Example

This script demonstrates how to use the vector database functionality
to store and search file embeddings using Google's Gemini API.
"""

import asyncio
import json
from typing import List, Dict, Any
from app.services.vector_service import vector_service
from app.services.ai_service import ai_service
from app.config import settings


async def example_upload_files():
    """Example: Upload files and store them in vector database"""
    print("=== Example: Upload Files to Vector Database ===")
    
    # Simulate file uploads
    sample_files = [
        {
            "filename": "business_strategy.pdf",
            "content": """
            Business Strategy Document
            
            Our company focuses on three key areas:
            1. Market expansion in emerging markets
            2. Product innovation and R&D
            3. Customer experience optimization
            
            Key metrics include:
            - Revenue growth: 25% YoY
            - Customer satisfaction: 4.8/5
            - Market share: 15% in target segments
            """,
            "content_type": "application/pdf"
        },
        {
            "filename": "growth_plan.txt",
            "content": """
            Growth Plan 2024
            
            Phase 1: Market Research (Q1)
            - Analyze competitor strategies
            - Identify new market opportunities
            - Conduct customer surveys
            
            Phase 2: Product Development (Q2)
            - Develop MVP for new features
            - Conduct beta testing
            - Gather user feedback
            
            Phase 3: Market Launch (Q3-Q4)
            - Launch marketing campaigns
            - Partner with key distributors
            - Monitor performance metrics
            """,
            "content_type": "text/plain"
        },
        {
            "filename": "financial_analysis.xlsx",
            "content": """
            Financial Analysis Report
            
            Revenue Projections:
            - Q1: $2.5M
            - Q2: $3.2M
            - Q3: $4.1M
            - Q4: $5.0M
            
            Key Financial Metrics:
            - Gross Margin: 65%
            - Operating Expenses: 35% of revenue
            - Net Profit Margin: 20%
            - Cash Flow: Positive from Q2
            """,
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    ]
    
    # Simulate playbook ID
    playbook_id = "example-playbook-123"
    
    print(f"Processing {len(sample_files)} files...")
    
    # Store files in vector database
    result = await vector_service.store_file_vectors(sample_files, playbook_id)
    
    if result["success"]:
        print(f"✓ Successfully stored {result['stored_count']} file vectors")
        print(f"Playbook ID: {result['playbook_id']}")
        
        # Display stored vectors info
        for vector in result["vectors"]:
            print(f"  - {vector['filename']} ({vector['content_type']})")
            print(f"    Size: {vector['file_size']} characters")
            print(f"    Embedding: {len(vector['embedding'])} dimensions")
    else:
        print(f"✗ Failed to store vectors: {result.get('error', 'Unknown error')}")
    
    return playbook_id


async def example_search_files():
    """Example: Search for similar files"""
    print("\n=== Example: Search Files Using Vector Similarity ===")
    
    # Search queries
    search_queries = [
        "market expansion strategy",
        "financial projections and revenue",
        "product development roadmap",
        "customer experience optimization"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        results = await vector_service.search_similar_files(query, limit=3)
        
        if results:
            print(f"Found {len(results)} similar files:")
            for result in results:
                similarity = result.get('similarity', 0)
                filename = result.get('filename', 'Unknown')
                print(f"  - {filename} (similarity: {similarity:.3f})")
        else:
            print("No similar files found")


async def example_get_playbook_files(playbook_id: str):
    """Example: Get all file vectors for a specific playbook"""
    print(f"\n=== Example: Get Files for Playbook {playbook_id} ===")
    
    file_vectors = await vector_service.get_file_vectors_by_playbook(playbook_id)
    
    if file_vectors:
        print(f"Found {len(file_vectors)} file vectors:")
        for vector in file_vectors:
            filename = vector.get('filename', 'Unknown')
            content_type = vector.get('content_type', 'Unknown')
            file_size = vector.get('file_size', 0)
            embedding_dim = len(vector.get('embedding', []))
            
            print(f"  - {filename}")
            print(f"    Type: {content_type}")
            print(f"    Size: {file_size} characters")
            print(f"    Embedding: {embedding_dim} dimensions")
            
            # Show metadata if available
            metadata = vector.get('metadata', {})
            if metadata:
                preview = metadata.get('content_preview', '')
                if preview:
                    print(f"    Preview: {preview[:100]}...")
    else:
        print("No file vectors found for this playbook")


async def example_embedding_quality():
    """Example: Test embedding quality and normalization"""
    print("\n=== Example: Embedding Quality Test ===")
    
    test_texts = [
        "This is a business strategy document about market expansion.",
        "Financial analysis shows strong revenue growth projections.",
        "Product development roadmap for Q2 2024 includes new features.",
        "Customer experience optimization through improved UX design."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: Creating embedding for text")
        print(f"Text: '{text[:50]}...'")
        
        embedding = await vector_service.create_file_embedding(
            text, f"test_{i}.txt", "text/plain"
        )
        
        # Check embedding properties
        import numpy as np
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  Embedding norm: {norm:.6f}")
        print(f"  Is normalized: {'Yes' if abs(norm - 1.0) < 0.01 else 'No'}")


async def example_similarity_comparison():
    """Example: Compare similarity between different texts"""
    print("\n=== Example: Similarity Comparison ===")
    
    # Test texts with different topics
    texts = [
        ("Business Strategy", "market expansion and growth strategy"),
        ("Financial Analysis", "revenue projections and financial metrics"),
        ("Product Development", "feature roadmap and development timeline"),
        ("Customer Experience", "user experience and customer satisfaction")
    ]
    
    # Create embeddings for all texts
    embeddings = []
    for title, text in texts:
        embedding = await vector_service.create_file_embedding(
            text, f"{title.lower().replace(' ', '_')}.txt", "text/plain"
        )
        embeddings.append((title, embedding))
    
    # Calculate similarities between all pairs
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    
    print("Similarity Matrix:")
    print("                  ", end="")
    for title, _ in embeddings:
        print(f"{title:15}", end="")
    print()
    
    for i, (title1, emb1) in enumerate(embeddings):
        print(f"{title1:15}", end="")
        for j, (title2, emb2) in enumerate(embeddings):
            similarity = cosine_similarity([emb1], [emb2])[0][0]
            print(f"{similarity:15.3f}", end="")
        print()


async def main():
    """Run all examples"""
    print("Vector Database Examples")
    print("=" * 50)
    
    try:
        # Test embedding quality first
        await example_embedding_quality()
        
        # Upload files to vector database
        playbook_id = await example_upload_files()
        
        # Search for similar files
        await example_search_files()
        
        # Get files for specific playbook
        await example_get_playbook_files(playbook_id)
        
        # Compare similarities
        await example_similarity_comparison()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully! 🎉")
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Make sure your Google API key is configured and database is set up.")


if __name__ == "__main__":
    asyncio.run(main()) 
