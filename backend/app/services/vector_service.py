import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import json
import uuid
from datetime import datetime
import numpy as np
from app.config import settings
from app.services.supabase_service import supabase_service


class VectorService:
    """Service for managing vector embeddings and vector database operations"""
    
    def __init__(self):
        self._embedding_model = None
        self._configured = False
    
    def _configure(self):
        """Lazy configuration of Gemini embedding model"""
        if not self._configured:
            genai.configure(api_key=settings.google_api_key)
            self._configured = True
    
    @property
    def embedding_model(self):
        """Lazy initialization of Gemini embedding model"""
        if self._embedding_model is None:
            self._configure()
            # Use the correct embedding model name as per Google's documentation
            self._embedding_model = genai.GenerativeModel('gemini-embedding-001')
        return self._embedding_model
    
    async def create_file_embedding(self, file_content: str, filename: str, content_type: str) -> List[float]:
        """
        Create vector embedding for a file using Google's Gemini embedding model
        
        Args:
            file_content: Text content of the file
            filename: Name of the file
            content_type: MIME type of the file
            
        Returns:
            List of float values representing the embedding vector
        """
        try:
            # Prepare text for embedding (limit to avoid token limits)
            embedding_text = f"File: {filename}\nType: {content_type}\nContent: {file_content[:6000]}"
            
            # Create embedding using Google's API
            embedding_result = self.embedding_model.embed_content(embedding_text)
            
            # Convert to list of floats and normalize
            embedding_vector = embedding_result.embedding
            
            # Normalize the embedding for better similarity calculations
            normalized_embedding = self._normalize_embedding(embedding_vector)
            
            return normalized_embedding
            
        except Exception as e:
            print(f"Error creating embedding for {filename}: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * settings.vector_dimension
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding vector for better similarity calculations
        
        Args:
            embedding: Raw embedding vector
            
        Returns:
            Normalized embedding vector
        """
        try:
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                normalized = embedding_array / norm
                return normalized.tolist()
            return embedding
        except Exception as e:
            print(f"Error normalizing embedding: {str(e)}")
            return embedding
    
    async def store_file_vectors(self, files: List[Dict[str, Any]], playbook_id: str) -> Dict[str, Any]:
        """
        Store file embeddings in vector database
        
        Args:
            files: List of file information with content, filename, content_type
            playbook_id: ID of the playbook these files belong to
            
        Returns:
            Dictionary with vector storage results
        """
        try:
            vector_records = []
            
            # Process each file and create embeddings
            for file_info in files:
                # Create embedding for the file
                embedding = await self.create_file_embedding(
                    file_info['content'],
                    file_info['filename'],
                    file_info['content_type']
                )
                
                # Create vector record
                vector_record = {
                    "id": str(uuid.uuid4()),
                    "playbook_id": playbook_id,
                    "filename": file_info['filename'],
                    "content_type": file_info['content_type'],
                    "embedding": embedding,
                    "file_size": len(file_info['content']),
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "original_filename": file_info['filename'],
                        "content_preview": file_info['content'][:200] + "..." if len(file_info['content']) > 200 else file_info['content']
                    }
                }
                
                vector_records.append(vector_record)
            
            # Store vectors in Supabase (using pgvector extension)
            stored_vectors = await self._store_vectors_in_database(vector_records)
            
            return {
                "success": True,
                "stored_count": len(stored_vectors),
                "vectors": stored_vectors,
                "playbook_id": playbook_id
            }
            
        except Exception as e:
            print(f"Error storing file vectors: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "stored_count": 0,
                "vectors": [],
                "playbook_id": playbook_id
            }
    
    async def _store_vectors_in_database(self, vector_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Store vector records in the database using Supabase
        
        Args:
            vector_records: List of vector records to store
            
        Returns:
            List of successfully stored vector records
        """
        try:
            stored_records = []
            
            for record in vector_records:
                # Store in the file_vectors table
                result = await supabase_service.client.table('file_vectors').insert({
                    "id": record["id"],
                    "playbook_id": record["playbook_id"],
                    "filename": record["filename"],
                    "content_type": record["content_type"],
                    "embedding": record["embedding"],
                    "file_size": record["file_size"],
                    "created_at": record["created_at"],
                    "metadata": record["metadata"]
                }).execute()
                
                if result.data:
                    stored_records.append(record)
            
            return stored_records
            
        except Exception as e:
            print(f"Error storing vectors in database: {str(e)}")
            return []
    
    async def search_similar_files(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for files similar to the query using vector similarity
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of similar files with similarity scores
        """
        try:
            # Create embedding for the query
            query_embedding = await self.create_file_embedding(query, "query", "text/plain")
            
            # Search using vector similarity in Supabase
            result = await supabase_service.client.rpc(
                'search_file_vectors',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.7,
                    'match_count': limit
                }
            ).execute()
            
            if result.data:
                return result.data
            else:
                return []
                
        except Exception as e:
            print(f"Error searching similar files: {str(e)}")
            return []
    
    async def get_file_vectors_by_playbook(self, playbook_id: str) -> List[Dict[str, Any]]:
        """
        Get all vector records for a specific playbook
        
        Args:
            playbook_id: ID of the playbook
            
        Returns:
            List of vector records for the playbook
        """
        try:
            result = await supabase_service.client.table('file_vectors').select(
                "*"
            ).eq("playbook_id", playbook_id).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting file vectors for playbook {playbook_id}: {str(e)}")
            return []
    
    async def delete_file_vectors(self, playbook_id: str) -> bool:
        """
        Delete all vector records for a specific playbook
        
        Args:
            playbook_id: ID of the playbook
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase_service.client.table('file_vectors').delete().eq(
                "playbook_id", playbook_id
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting file vectors for playbook {playbook_id}: {str(e)}")
            return False


# Global instance
vector_service = VectorService() 
