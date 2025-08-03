from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import uuid
from app.config import settings


class SupabaseService:
    def __init__(self):
        self._client = None
        self._service_client = None
    
    @property
    def client(self) -> Client:
        """Lazy initialization of Supabase client"""
        if self._client is None:
            self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Lazy initialization of Supabase service client"""
        if self._service_client is None:
            self._service_client = create_client(
                settings.supabase_url, settings.supabase_service_role_key
            )
        return self._service_client
    
    async def create_user(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Create a new user in Supabase Auth"""
        try:
            response = self.service_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "user_metadata": {"full_name": full_name}
            })
            return response.user
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": "dummy"  # We'll handle auth separately
            })
            return None  # This will fail, but we can get user info differently
        except:
            # Try to get user from users table
            response = self.client.table("users").select("*").eq("email", email).execute()
            if response.data:
                return response.data[0]
            return None
    
    async def create_playbook(self, playbook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new playbook in the database"""
        try:
            playbook_id = str(uuid.uuid4())
            playbook_data["id"] = playbook_id
            playbook_data["created_at"] = datetime.utcnow().isoformat()
            playbook_data["updated_at"] = datetime.utcnow().isoformat()
            playbook_data["owner_id"] = playbook_data.get("owner_id", None) or str(uuid.uuid4())
            response = self.client.table("playbooks").insert(playbook_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to create playbook: {str(e)}")
    
    async def get_playbook(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        """Get a playbook by ID"""
        try:
            response = self.client.table("playbooks").select("*").eq("id", playbook_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get playbook: {str(e)}")
    
    async def get_playbooks(self, user_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all playbooks with optional filtering"""
        try:
            query = self.client.table("playbooks").select("*")
            
            if user_id:
                query = query.eq("owner_id", user_id)
            
            response = query.range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get playbooks: {str(e)}")
    
    async def update_playbook(self, playbook_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a playbook"""
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table("playbooks").update(update_data).eq("id", playbook_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to update playbook: {str(e)}")
    
    async def delete_playbook(self, playbook_id: str) -> bool:
        """Delete a playbook"""
        try:
            response = self.client.table("playbooks").delete().eq("id", playbook_id).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete playbook: {str(e)}")
    
    async def search_playbooks_vector(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search playbooks using vector similarity"""
        try:
            # Using pgvector cosine similarity
            response = self.client.rpc(
                "match_playbooks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.7,
                    "match_count": limit
                }
            ).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to search playbooks: {str(e)}")
    
    async def search_playbooks_text(self, query: str, tags: Optional[List[str]] = None, 
                                   stage: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search playbooks using text search"""
        try:
            query_builder = self.client.table("playbooks").select("*")
            
            # Text search in title and description
            query_builder = query_builder.or_(f"title.ilike.%{query}%,description.ilike.%{query}%")
            
            # Filter by tags if provided
            if tags:
                for tag in tags:
                    query_builder = query_builder.contains("tags", [tag])
            
            # Filter by stage if provided
            if stage:
                query_builder = query_builder.eq("stage", stage)
            
            response = query_builder.range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to search playbooks: {str(e)}")
    
    async def upload_file_to_storage(self, file_path: str, file_content: bytes, content_type: str) -> str:
        """Upload file to Supabase Storage"""
        try:
            response = self.client.storage.from_(settings.storage_bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type}
            )
            return f"{settings.supabase_url}/storage/v1/object/public/{settings.storage_bucket_name}/{file_path}"
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def delete_file_from_storage(self, file_path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            self.client.storage.from_(settings.storage_bucket_name).remove([file_path])
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for a file"""
        try:
            response = self.client.storage.from_(settings.storage_bucket_name).get_public_url(file_path)
            return response
        except Exception as e:
            raise Exception(f"Failed to get file URL: {str(e)}")


# Global instance
supabase_service = SupabaseService() 
