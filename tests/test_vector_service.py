import pytest
import asyncio
from app.services.vector_service import vector_service
from app.config import settings


class TestVectorService:
    """Test cases for the VectorService"""
    
    @pytest.mark.asyncio
    async def test_create_file_embedding(self):
        """Test creating embeddings for files"""
        # Test with simple text content
        test_content = "This is a test document about business strategy and growth."
        test_filename = "test_document.txt"
        test_content_type = "text/plain"
        
        embedding = await vector_service.create_file_embedding(
            test_content, test_filename, test_content_type
        )
        
        # Verify embedding is created and has correct dimension
        assert isinstance(embedding, list)
        assert len(embedding) == settings.vector_dimension
        assert all(isinstance(x, float) for x in embedding)
        
        # Verify embedding is normalized (norm should be close to 1)
        import numpy as np
        norm = np.linalg.norm(np.array(embedding))
        assert abs(norm - 1.0) < 0.01  # Allow small tolerance
    
    @pytest.mark.asyncio
    async def test_normalize_embedding(self):
        """Test embedding normalization"""
        # Test with a simple vector
        test_embedding = [1.0, 2.0, 3.0, 4.0, 5.0]
        normalized = vector_service._normalize_embedding(test_embedding)
        
        # Verify normalization
        import numpy as np
        norm = np.linalg.norm(np.array(normalized))
        assert abs(norm - 1.0) < 0.01
    
    @pytest.mark.asyncio
    async def test_store_file_vectors(self):
        """Test storing file vectors in database"""
        # Mock file data
        test_files = [
            {
                "filename": "test1.txt",
                "content": "This is a test document about business strategy.",
                "content_type": "text/plain"
            },
            {
                "filename": "test2.pdf",
                "content": "This is another test document about growth and scaling.",
                "content_type": "application/pdf"
            }
        ]
        
        test_playbook_id = "test-playbook-123"
        
        # Test vector storage (this will fail if database is not set up)
        result = await vector_service.store_file_vectors(test_files, test_playbook_id)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "success" in result
        assert "stored_count" in result
        assert "vectors" in result
        assert "playbook_id" in result
        assert result["playbook_id"] == test_playbook_id
    
    @pytest.mark.asyncio
    async def test_search_similar_files(self):
        """Test searching for similar files"""
        query = "business strategy and growth"
        
        # Test search (this will fail if database is not set up)
        results = await vector_service.search_similar_files(query, limit=5)
        
        # Verify result structure
        assert isinstance(results, list)
        # Results might be empty if no data in database, which is fine for testing
    
    @pytest.mark.asyncio
    async def test_get_file_vectors_by_playbook(self):
        """Test getting file vectors for a specific playbook"""
        test_playbook_id = "test-playbook-123"
        
        # Test getting file vectors (this will fail if database is not set up)
        results = await vector_service.get_file_vectors_by_playbook(test_playbook_id)
        
        # Verify result structure
        assert isinstance(results, list)
        # Results might be empty if no data in database, which is fine for testing


if __name__ == "__main__":
    # Run basic tests
    async def run_tests():
        test_service = TestVectorService()
        
        print("Testing file embedding creation...")
        await test_service.test_create_file_embedding()
        print("✓ File embedding creation test passed")
        
        print("Testing embedding normalization...")
        await test_service.test_normalize_embedding()
        print("✓ Embedding normalization test passed")
        
        print("Testing vector storage...")
        await test_service.test_store_file_vectors()
        print("✓ Vector storage test passed")
        
        print("Testing file search...")
        await test_service.test_search_similar_files()
        print("✓ File search test passed")
        
        print("Testing get file vectors...")
        await test_service.test_get_file_vectors_by_playbook()
        print("✓ Get file vectors test passed")
        
        print("\nAll tests passed! 🎉")
    
    asyncio.run(run_tests()) 
