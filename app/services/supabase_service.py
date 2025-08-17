from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import json
import math
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
    
    async def create_user(self, email: str, password: str, full_name: str, hashed_password: str) -> Dict[str, Any]:
        """Create a new user in Supabase Auth and Users table"""
        try:
            # Generate a UUID for the user
            user_id = str(uuid.uuid4())
            
            # Create user directly in users table with hashed password
            user_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "hashed_password": hashed_password,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Insert into users table
            table_response = self.client.table("users").insert(user_data).execute()
            
            if table_response.data:
                # Return user data in the expected format
                return {
                    "id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "created_at": user_data["created_at"]
                }
            return None
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from users table"""
        try:
            # Get user from users table
            response = self.client.table("users").select("*").eq("email", email).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user by email: {str(e)}")
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
    
    async def get_playbooks_by_user_detailed(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get playbooks by user with detailed information including file counts and processing status"""
        try:
            # Get playbooks with file counts using a join
            response = self.client.table("playbooks").select("""
                *,
                playbook_files!playbook_files_playbook_id_fkey (
                    id,
                    file_name,
                    file_type
                )
            """).eq("owner_id", user_id).range(offset, offset + limit - 1).execute()
            
            # Process the results to add file counts and processing status
            detailed_playbooks = []
            for playbook in response.data:
                # Count files
                file_count = len(playbook.get("playbook_files", []))
                
                # Determine processing status
                has_summary = bool(playbook.get("summary"))
                has_embedding = bool(playbook.get("vector_embedding"))
                
                if has_summary and has_embedding:
                    processing_status = "completed"
                elif has_summary or has_embedding:
                    processing_status = "processing"
                else:
                    processing_status = "processing"
                
                # Add additional metadata
                playbook["file_count"] = file_count
                playbook["processing_status"] = processing_status
                playbook["has_summary"] = has_summary
                playbook["has_embedding"] = has_embedding
                
                # Remove the detailed file list to keep response size manageable
                if "playbook_files" in playbook:
                    del playbook["playbook_files"]
                
                detailed_playbooks.append(playbook)
            
            return detailed_playbooks
        except Exception as e:
            raise Exception(f"Failed to get detailed playbooks by user: {str(e)}")
    
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
            print(f"🔍 Searching playbooks with embedding of {len(query_embedding)} dimensions")
            
            # Using pgvector cosine similarity
            response = self.client.rpc(
                "match_playbooks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.3,
                    "match_count": limit
                }
            ).execute()
            
            print(f"✅ Vector search response: {len(response.data) if response.data else 0} results")
            
            # Debug: Print the first result to see what fields are available
            if response.data:
                print(f"🔍 Debug - First result fields: {list(response.data[0].keys())}")
                print(f"🔍 Debug - First result: {response.data[0]}")
                print(f"🔍 Debug - Similarity value: {response.data[0].get('similarity')} (type: {type(response.data[0].get('similarity'))})")
            
            if response.data:
                # Transform the results to match expected format
                transformed_results = []
                for result in response.data:
                    # Handle missing datetime fields gracefully
                    created_at = result.get("created_at")
                    updated_at = result.get("updated_at")
                    
                    # If datetime fields are missing, use current time
                    if not created_at:
                        created_at = datetime.utcnow().isoformat()
                    if not updated_at:
                        updated_at = datetime.utcnow().isoformat()
                    
                    # Handle NaN similarity scores
                    similarity = result["similarity"]
                    if similarity == 'NaN' or (isinstance(similarity, float) and math.isnan(similarity)):
                        similarity = 0.0  # Default to 0 similarity for NaN values
                    elif isinstance(similarity, str):
                        try:
                            similarity = float(similarity)
                            if math.isnan(similarity):
                                similarity = 0.0
                        except (ValueError, TypeError):
                            similarity = 0.0
                    
                    transformed_results.append({
                        "playbook": {
                            "id": result["id"],
                            "title": result["title"],
                            "description": result["description"],
                            "tags": result["tags"],
                            "stage": result["stage"],
                            "owner_id": result["owner_id"],
                            "version": result["version"],
                            "files": result["files"],
                            "summary": result["summary"],
                            "created_at": created_at,
                            "updated_at": updated_at
                        },
                        "similarity": similarity
                    })
                return transformed_results
            else:
                print("⚠️ No results found in vector search")
                return []
                
        except Exception as e:
            print(f"❌ Vector search error: {str(e)}")
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

    async def validate_user_exists(self, user_id: str) -> bool:
        """Validate if user exists in the database"""
        try:
            # Get the full user record to ensure it exists and is valid
            response = self.client.table("users").select("*").eq("id", user_id).execute()
            if len(response.data) == 0:
                print(f"No user found with ID: {user_id}")
                return False
            
            # Additional validation - ensure the user record is complete
            user = response.data[0]
            if not user.get('id') or not user.get('email'):
                print(f"Incomplete user record for ID {user_id}: {user}")
                return False
                
            print(f"User validation successful for {user_id}: {user.get('email')}")
            return True
        except Exception as e:
            print(f"User validation error for {user_id}: {str(e)}")
            return False

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID for debugging purposes"""
        try:
            response = self.client.table("users").select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by ID {user_id}: {str(e)}")
            return None

    async def create_user_playbook_fork(self, user_id: str, original_playbook_id: str, forked_playbook_id: str = None, base_version: int = 1, license: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user playbook fork entry"""
        try:
            print(f"Creating fork with user_id: {user_id}, playbook_id: {original_playbook_id}, forked_playbook_id: {forked_playbook_id}")
            
            # Double-check user exists before creating fork
            user_check = await self.validate_user_exists(user_id)
            if not user_check:
                raise Exception(f"User {user_id} does not exist in database")
            
            # Start with basic fork data
            fork_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "original_playbook_id": original_playbook_id,
                "forked_at": datetime.utcnow().isoformat(),
                "last_updated_at": datetime.utcnow().isoformat(),
                "version": "v1",
                "license": license,
                "status": "active"
            }
            
            # Add forked_playbook_id if provided
            if forked_playbook_id:
                fork_data["forked_playbook_id"] = forked_playbook_id
            
            # Try to add version columns if they exist
            try:
                # Check if the table has the version columns by trying to insert with them
                fork_data_with_version = fork_data.copy()
                fork_data_with_version.update({
                    "base_version": base_version,
                    "last_sync_version": base_version
                })
                
                print(f"Attempting to insert with version columns: {fork_data_with_version}")
                response = self.client.table("user_playbooks").insert(fork_data_with_version).execute()
                
                if not response.data:
                    raise Exception("No data returned from fork creation")
                    
                print(f"Fork created successfully with version columns: {response.data[0]['id']}")
                return response.data[0]
                
            except Exception as version_error:
                print(f"Version columns not available, trying without: {str(version_error)}")
                
                # Fallback to basic fork data without version columns
                print(f"Inserting basic fork data: {fork_data}")
                response = self.client.table("user_playbooks").insert(fork_data).execute()
                
                if not response.data:
                    raise Exception("No data returned from fork creation")
                    
                print(f"Fork created successfully without version columns: {response.data[0]['id']}")
                return response.data[0]
                
        except Exception as e:
            print(f"Fork creation error: {str(e)}")
            raise Exception(f"Failed to create user playbook fork: {str(e)}")

    async def get_playbook_files(self, playbook_id: str) -> List[Dict[str, Any]]:
        """Get all active files associated with a playbook"""
        try:
            response = self.client.table("playbook_files").select("*").eq("playbook_id", playbook_id).eq("is_active", True).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get playbook files: {str(e)}")
    
    async def get_playbook_files_by_version(self, playbook_id: str, version_number: int) -> List[Dict[str, Any]]:
        """Get files for a specific version of a playbook"""
        try:
            response = self.client.table("playbook_files").select("*").eq("playbook_id", playbook_id).eq("version_created", version_number).eq("is_active", True).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get playbook files by version: {str(e)}")
    
    async def create_playbook_file(self, playbook_file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new playbook file entry"""
        try:
            file_id = str(uuid.uuid4())
            playbook_file_data["id"] = file_id
            playbook_file_data["created_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("playbook_files").insert(playbook_file_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to create playbook file: {str(e)}")

    async def create_user_playbook_file(self, user_playbook_file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user playbook file entry"""
        try:
            file_id = str(uuid.uuid4())
            user_playbook_file_data["id"] = file_id
            
            # Try to add timestamp fields if they exist
            try:
                user_playbook_file_data.update({
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "last_modified_at": datetime.utcnow().isoformat()
                })
                
                response = self.client.table("user_playbook_files").insert(user_playbook_file_data).execute()
                return response.data[0] if response.data else None
                
            except Exception as timestamp_error:
                # If timestamp columns don't exist, try without them
                print(f"Timestamp columns not available, trying without: {str(timestamp_error)}")
                
                # Remove timestamp fields and try again
                user_playbook_file_data.pop("uploaded_at", None)
                user_playbook_file_data.pop("last_modified_at", None)
                
                response = self.client.table("user_playbook_files").insert(user_playbook_file_data).execute()
                return response.data[0] if response.data else None
                
        except Exception as e:
            raise Exception(f"Failed to create user playbook file: {str(e)}")
    
    async def update_playbook_file(self, file_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a playbook file entry"""
        try:
            response = self.client.table("playbook_files").update(update_data).eq("id", file_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to update playbook file: {str(e)}")
    
    async def delete_playbook_file(self, file_id: str) -> bool:
        """Delete a playbook file entry"""
        try:
            response = self.client.table("playbook_files").delete().eq("id", file_id).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete playbook file: {str(e)}")
    
    async def get_playbook_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific playbook file by ID"""
        try:
            response = self.client.table("playbook_files").select("*").eq("id", file_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get playbook file: {str(e)}")
    
    async def upload_playbook_file_to_storage(self, file_content: bytes, storage_path: str, bucket: str = "playbooks") -> str:
        """Upload a file to Supabase Storage and return the storage path"""
        try:
            response = self.client.storage.from_(bucket).upload(storage_path, file_content)
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Storage upload error: {response.error}")
            return storage_path
        except Exception as e:
            raise Exception(f"Failed to upload file to storage: {str(e)}")
    
    async def delete_file_from_storage(self, storage_path: str, bucket: str = "playbooks") -> bool:
        """Delete a file from Supabase Storage"""
        try:
            response = self.client.storage.from_(bucket).remove([storage_path])
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file from storage: {str(e)}")
    
    # ==========================================
    # Pull Request Methods
    # ==========================================
    
    async def create_pull_request(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pull request"""
        try:
            pr_id = str(uuid.uuid4())
            pr_data["id"] = pr_id
            pr_data["created_at"] = datetime.utcnow().isoformat()
            pr_data["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("pull_requests").insert(pr_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to create pull request: {str(e)}")
    
    async def get_pull_request(self, pr_id: str) -> Optional[Dict[str, Any]]:
        """Get pull request by ID"""
        try:
            response = self.client.table("pull_requests").select("*").eq("id", pr_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get pull request: {str(e)}")
    
    async def update_pull_request(self, pr_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a pull request"""
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table("pull_requests").update(update_data).eq("id", pr_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to update pull request: {str(e)}")
    
    async def list_pull_requests(
        self, 
        playbook_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List pull requests with optional filters"""
        try:
            query = self.client.table("pull_requests").select("*")
            
            if playbook_id:
                query = query.eq("target_playbook_id", playbook_id)
            if user_id:
                query = query.eq("user_id", user_id)
            if status:
                query = query.eq("status", status)
            
            query = query.order("created_at", desc=True).limit(limit).offset(offset)
            
            response = query.execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to list pull requests: {str(e)}")
    
    async def create_pull_request_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pull request file record with comprehensive schema"""
        try:
            file_id = str(uuid.uuid4())
            file_data["id"] = file_id
            file_data["created_at"] = datetime.utcnow().isoformat()
            
            # Ensure required fields are present with defaults
            file_data.setdefault("change_type", "modified")
            file_data.setdefault("risk_flags", [])
            file_data.setdefault("confidence", 0.8)
            
            response = self.client.table("pull_request_files").insert(file_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to create pull request file: {str(e)}")
    
    async def get_pull_request_files(self, pr_id: str) -> List[Dict[str, Any]]:
        """Get all files for a pull request"""
        try:
            response = self.client.table("pull_request_files").select("*").eq("pr_id", pr_id).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get pull request files: {str(e)}")
    
    async def get_user_playbook_file_by_path(self, user_playbook_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Get user playbook file by file path"""
        try:
            response = self.client.table("user_playbook_files").select("*").eq("user_playbook_id", user_playbook_id).eq("file_path", file_path).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get user playbook file by path: {str(e)}")
    
    async def get_playbook_file_by_name(self, playbook_id: str, file_name: str) -> Optional[Dict[str, Any]]:
        """Get playbook file by file name"""
        try:
            response = self.client.table("playbook_files").select("*").eq("playbook_id", playbook_id).eq("file_name", file_name).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get playbook file by name: {str(e)}")
    
    async def list_playbooks(self, owner_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List playbooks with optional owner filter"""
        try:
            query = self.client.table("playbooks").select("*")
            
            if owner_id:
                query = query.eq("owner_id", owner_id)
            
            query = query.order("created_at", desc=True).limit(limit)
            
            response = query.execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to list playbooks: {str(e)}")
    
    # ==========================================
    # Fork Methods (using forks table)
    # ==========================================
    
    async def get_fork(self, fork_id: str) -> Optional[Dict[str, Any]]:
        """Get fork by ID"""
        try:
            response = self.client.table("forks").select("*").eq("id", fork_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get fork: {str(e)}")
    
    async def create_fork(self, fork_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new fork"""
        try:
            fork_id = str(uuid.uuid4())
            fork_data["id"] = fork_id
            fork_data["created_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("forks").insert(fork_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to create fork: {str(e)}")
    
    async def list_forks(self, user_id: Optional[str] = None, playbook_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List forks with optional filters"""
        try:
            query = self.client.table("forks").select("*")
            
            if user_id:
                query = query.eq("user_id", user_id)
            if playbook_id:
                query = query.eq("playbook_id", playbook_id)
            
            query = query.order("created_at", desc=True)
            
            response = query.execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to list forks: {str(e)}")

    async def copy_playbook_files_with_version(self, user_playbook_id: str, original_files: List[Dict[str, Any]], version_number: int = 1) -> List[Dict[str, Any]]:
        """Copy files from original playbook to user playbook with version tracking"""
        try:
            copied_files = []
            
            for original_file in original_files:
                # Generate new storage path for the copied file
                new_file_path = f"user_playbooks/{user_playbook_id}/{original_file['file_name']}"
                
                # Extract the actual storage path from the original file
                # storage_path might be a full URL or just a path
                original_storage_path = original_file['storage_path']
                if original_storage_path.startswith('http'):
                    # Extract path from URL: remove base URL and bucket name
                    path_parts = original_storage_path.split('/')
                    bucket_index = next(i for i, part in enumerate(path_parts) if part == settings.storage_bucket_name)
                    original_storage_path = '/'.join(path_parts[bucket_index + 1:])
                
                # Download original file content from storage
                try:
                    file_content = self.client.storage.from_(settings.storage_bucket_name).download(original_storage_path)
                except Exception as download_error:
                    raise Exception(f"Failed to download original file {original_storage_path}: {str(download_error)}")
                
                # Determine content type based on file extension
                file_extension = original_file['file_name'].split('.')[-1].lower()
                content_type_map = {
                    'pdf': 'application/pdf',
                    'md': 'text/markdown',
                    'txt': 'text/plain',
                    'csv': 'text/csv',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg'
                }
                content_type = content_type_map.get(file_extension, 'application/octet-stream')
                
                # Upload to new location in user_playbooks storage
                new_storage_url = await self.upload_file_to_storage(
                    new_file_path, 
                    file_content, 
                    content_type
                )
                
                # Create new file entry in user_playbook_files table with version tracking
                # Start with basic required fields
                file_data = {
                    "id": str(uuid.uuid4()),
                    "user_playbook_id": user_playbook_id,
                    "file_path": original_file['file_name'],  # Relative path within the playbook
                    "file_type": original_file['file_type'],
                    "storage_path": new_storage_url,  # Full storage URL
                    "version": "v1",
                    "version_created": version_number,  # Version tracking
                    "is_active": True
                }
                
                # Try to add optional timestamp fields if they exist
                try:
                    file_data.update({
                        "uploaded_at": datetime.utcnow().isoformat(),
                        "last_modified_at": datetime.utcnow().isoformat()
                    })
                    
                    response = self.client.table("user_playbook_files").insert(file_data).execute()
                    if response.data:
                        copied_files.append(response.data[0])
                        
                except Exception as timestamp_error:
                    # If timestamp columns don't exist, try without them
                    print(f"Timestamp columns not available, trying without: {str(timestamp_error)}")
                    
                    # Remove timestamp fields and try again
                    file_data.pop("uploaded_at", None)
                    file_data.pop("last_modified_at", None)
                    
                    response = self.client.table("user_playbook_files").insert(file_data).execute()
                    if response.data:
                        copied_files.append(response.data[0])
            
            return copied_files
        except Exception as e:
            raise Exception(f"Failed to copy playbook files: {str(e)}")
    
    async def copy_playbook_files(self, user_playbook_id: str, original_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Copy files from original playbook to user playbook (legacy method)"""
        return await self.copy_playbook_files_with_version(user_playbook_id, original_files, 1)

    async def copy_playbook_files_to_new_playbook(self, new_playbook_id: str, original_files: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Copy files from original playbook to a new playbook record in the playbooks table"""
        try:
            copied_files = []
            
            for original_file in original_files:
                # Generate new storage path for the copied file
                new_file_path = f"playbook/{new_playbook_id}/{user_id}/v1/{original_file['file_name']}"
                
                # Extract the actual storage path from the original file
                # storage_path might be a full URL or just a path
                original_storage_path = original_file['storage_path']
                if original_storage_path.startswith('http'):
                    # Extract path from URL: remove base URL and bucket name
                    path_parts = original_storage_path.split('/')
                    bucket_index = next(i for i, part in enumerate(path_parts) if part == settings.storage_bucket_name)
                    original_storage_path = '/'.join(path_parts[bucket_index + 1:])
                
                # Download original file content from storage
                try:
                    file_content = self.client.storage.from_(settings.storage_bucket_name).download(original_storage_path)
                except Exception as download_error:
                    raise Exception(f"Failed to download original file {original_storage_path}: {str(download_error)}")
                
                # Determine content type based on file extension
                file_extension = original_file['file_name'].split('.')[-1].lower()
                content_type_map = {
                    'pdf': 'application/pdf',
                    'md': 'text/markdown',
                    'txt': 'text/plain',
                    'csv': 'text/csv',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg'
                }
                content_type = content_type_map.get(file_extension, 'application/octet-stream')
                
                # Upload to new location in playbook storage
                new_storage_url = await self.upload_file_to_storage(
                    new_file_path, 
                    file_content, 
                    content_type
                )
                
                # Create new file entry in playbook_files table
                file_data = {
                    "id": str(uuid.uuid4()),
                    "playbook_id": new_playbook_id,
                    "file_name": original_file['file_name'],
                    "file_type": original_file['file_type'],
                    "storage_path": new_storage_url,
                    "uploaded_by": user_id,
                    "version_created": 1,  # Initial version for the new playbook
                    "is_active": True
                }
                
                # Try to add optional timestamp fields if they exist
                try:
                    file_data.update({
                        "uploaded_at": datetime.utcnow().isoformat(),
                        "last_modified_at": datetime.utcnow().isoformat()
                    })
                    
                    response = self.client.table("playbook_files").insert(file_data).execute()
                    if response.data:
                        copied_files.append(response.data[0])
                        
                except Exception as timestamp_error:
                    # If timestamp columns don't exist, try without them
                    print(f"Timestamp columns not available, trying without: {str(timestamp_error)}")
                    
                    # Remove timestamp fields and try again
                    file_data.pop("uploaded_at", None)
                    file_data.pop("last_modified_at", None)
                    
                    response = self.client.table("playbook_files").insert(file_data).execute()
                    if response.data:
                        copied_files.append(response.data[0])
            
            return copied_files
        except Exception as e:
            raise Exception(f"Failed to copy playbook files to new playbook: {str(e)}")

    async def get_user_playbook(self, user_playbook_id: str) -> Optional[Dict[str, Any]]:
        """Get a user playbook by ID with original playbook details"""
        try:
            response = self.client.table("user_playbooks").select("""
                *,
                playbooks!user_playbooks_original_playbook_id_fkey (
                    id, title, description, tags, stage, version, created_at
                )
            """).eq("id", user_playbook_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get user playbook: {str(e)}")

    async def get_user_playbook_files(self, user_playbook_id: str) -> List[Dict[str, Any]]:
        """Get all files associated with a user playbook"""
        try:
            response = self.client.table("user_playbook_files").select("*").eq("user_playbook_id", user_playbook_id).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get user playbook files: {str(e)}")

    async def upload_user_playbook_file(self, user_playbook_id: str, file_name: str, file_content: bytes, file_type: str, content_type: str) -> Dict[str, Any]:
        """Upload a new file to a user playbook"""
        try:
            # Generate storage path for the file
            file_path = f"user_playbooks/{user_playbook_id}/{file_name}"
            
            # Upload to storage
            storage_url = await self.upload_file_to_storage(file_path, file_content, content_type)
            
            # Create file entry in database
            file_data = {
                "id": str(uuid.uuid4()),
                "user_playbook_id": user_playbook_id,
                "file_path": file_name,
                "file_type": file_type,
                "storage_path": storage_url,
                "uploaded_at": datetime.utcnow().isoformat(),
                "last_modified_at": datetime.utcnow().isoformat(),
                "version": "v1"
            }
            
            response = self.client.table("user_playbook_files").insert(file_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to upload user playbook file: {str(e)}")

    async def delete_user_playbook_file(self, file_id: str) -> bool:
        """Delete a user playbook file"""
        try:
            # Get file info first
            file_response = self.client.table("user_playbook_files").select("storage_path").eq("id", file_id).execute()
            if not file_response.data:
                return False
            
            storage_path = file_response.data[0]['storage_path']
            
            # Extract file path from storage URL
            if storage_path.startswith('http'):
                path_parts = storage_path.split('/')
                bucket_index = next(i for i, part in enumerate(path_parts) if part == settings.storage_bucket_name)
                file_path = '/'.join(path_parts[bucket_index + 1:])
            else:
                file_path = storage_path
            
            # Delete from storage
            await self.delete_file_from_storage(file_path)
            
            # Delete from database
            self.client.table("user_playbook_files").delete().eq("id", file_id).execute()
            
            return True
        except Exception as e:
            raise Exception(f"Failed to delete user playbook file: {str(e)}")

    async def delete_user_playbook_files(self, user_playbook_id: str) -> bool:
        """Delete all files for a user playbook"""
        try:
            # Delete all files from database
            response = self.client.table("user_playbook_files").delete().eq("user_playbook_id", user_playbook_id).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete user playbook files: {str(e)}")

    async def delete_user_playbook(self, user_playbook_id: str) -> bool:
        """Delete a user playbook entry"""
        try:
            response = self.client.table("user_playbooks").delete().eq("id", user_playbook_id).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete user playbook: {str(e)}")

    async def get_user_playbooks(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all user playbooks for a specific user"""
        try:
            response = self.client.table("user_playbooks").select("""
                *,
                playbooks!user_playbooks_original_playbook_id_fkey (
                    id, title, description, tags, stage, version, created_at
                )
            """).eq("user_id", user_id).range(offset, offset + limit - 1).execute()
            
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get user playbooks: {str(e)}")

    async def update_user_playbook(self, user_playbook_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user playbook entry"""
        try:
            update_data["last_updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table("user_playbooks").update(update_data).eq("id", user_playbook_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to update user playbook: {str(e)}")

    async def get_playbooks_with_fork_info(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get playbooks owned by user with fork information"""
        try:
            # Get playbooks owned by user
            owned_playbooks = await self.get_playbooks_by_user_detailed(user_id, limit, offset)
            
            # Get fork count for each playbook
            enhanced_playbooks = []
            for playbook in owned_playbooks:
                fork_count = await self.get_playbook_fork_count(playbook['id'])
                playbook['fork_count'] = fork_count
                # playbook['is_forked'] = playbook
                enhanced_playbooks.append(playbook)
            
            return enhanced_playbooks
        except Exception as e:
            raise Exception(f"Failed to get playbooks with fork info: {str(e)}")

    async def get_user_playbooks_with_fork_info(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get playbooks forked by user with fork information"""
        try:
            # Get forked playbooks
            forked_playbooks = await self.get_user_playbooks(user_id, limit, offset)
            
            # Enhance with fork information
            enhanced_forks = []
            for fork in forked_playbooks:
                original_playbook = fork.get('playbooks', {})
                if original_playbook:
                    # Get fork count for the original playbook
                    fork_count = await self.get_playbook_fork_count(original_playbook['id'])
                    
                    # Create enhanced playbook data
                    enhanced_playbook = {
                        **original_playbook,
                        'fork_count': fork_count,
                        'is_forked': True,
                        'forked_at': fork['forked_at'],
                        'original_playbook_id': original_playbook['id'],
                        'user_playbook_id': fork['id']
                    }
                    enhanced_forks.append(enhanced_playbook)
            
            return enhanced_forks
        except Exception as e:
            raise Exception(f"Failed to get user playbooks with fork info: {str(e)}")

    async def get_combined_user_playbooks(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get both owned and forked playbooks for a user"""
        try:
            # Get owned playbooks
            owned_playbooks = await self.get_playbooks_with_fork_info(user_id, limit // 2, offset)
            
            # Get forked playbooks
            forked_playbooks = await self.get_user_playbooks_with_fork_info(user_id, limit // 2, offset)
            
            # Combine and sort by most recent
            combined = owned_playbooks + forked_playbooks
            combined.sort(key=lambda x: x.get('updated_at', x.get('forked_at', x.get('created_at'))), reverse=True)
            
            return combined[:limit]
        except Exception as e:
            raise Exception(f"Failed to get combined user playbooks: {str(e)}")

    async def get_playbook_fork_count(self, playbook_id: str) -> int:
        """Get the number of times a playbook has been forked"""
        try:
            response = self.client.table("user_playbooks").select("id", count="exact").eq("original_playbook_id", playbook_id).execute()
            return response.count or 0
        except Exception as e:
            print(f"Error getting fork count for playbook {playbook_id}: {str(e)}")
            return 0

    async def get_playbook_forks(self, playbook_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get detailed information about users who forked a playbook"""
        try:
            response = self.client.table("user_playbooks").select("*").eq("original_playbook_id", playbook_id).range(offset, offset + limit - 1).execute()
            
            # Get user information separately for each fork
            valid_forks = []
            for fork in response.data:
                try:
                    # Get user information separately
                    user_response = self.client.table("users").select("id, email, full_name").eq("id", fork['user_id']).execute()
                    user_info = user_response.data[0] if user_response.data else {}
                    
                    # Only include forks with valid user data
                    if user_info.get('id') and user_info.get('email'):
                        # Add user info to the fork data
                        fork['users'] = user_info
                        valid_forks.append(fork)
                        
                except Exception as user_error:
                    print(f"Error getting user info for fork {fork.get('id')}: {str(user_error)}")
                    continue
            
            return valid_forks
        except Exception as e:
            print(f"Error in get_playbook_forks: {str(e)}")
            return []

    async def get_playbook_detailed(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed playbook information including fork data"""
        try:
            # Get basic playbook info
            playbook = await self.get_playbook(playbook_id)
            if not playbook:
                return None
            
            # Get fork count
            fork_count = await self.get_playbook_fork_count(playbook_id)
            
            # Get fork details
            forks = await self.get_playbook_forks(playbook_id, limit=10)
            
            # Enhance playbook with fork information
            playbook['fork_count'] = fork_count
            playbook['forks'] = forks
            
            return playbook
        except Exception as e:
            raise Exception(f"Failed to get detailed playbook: {str(e)}")

    async def get_user_notifications(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get notifications for a user (fork events on their playbooks)"""
        try:
            # Get playbooks owned by user
            owned_playbooks = await self.get_playbooks_by_user_detailed(user_id, 1000, 0)
            owned_playbook_ids = [p['id'] for p in owned_playbooks]
            
            if not owned_playbook_ids:
                return []
            
            # Get recent forks of user's playbooks (simplified query)
            response = self.client.table("user_playbooks").select("*").in_("original_playbook_id", owned_playbook_ids).range(offset, offset + limit - 1).order("forked_at", desc=True).execute()
            
            # Transform into notification format with separate queries for user and playbook data
            notifications = []
            for fork in response.data:
                try:
                    # Get user information separately
                    user_response = self.client.table("users").select("id, email, full_name").eq("id", fork['user_id']).execute()
                    user_info = user_response.data[0] if user_response.data else {}
                    
                    # Get playbook information separately
                    playbook_response = self.client.table("playbooks").select("id, title").eq("id", fork['original_playbook_id']).execute()
                    playbook_info = playbook_response.data[0] if playbook_response.data else {}
                    
                    # Validate required fields
                    if not all([
                        user_info.get('id'),
                        user_info.get('email'),
                        playbook_info.get('id'),
                        playbook_info.get('title')
                    ]):
                        print(f"Skipping notification due to missing data for fork {fork['id']}")
                        continue
                    
                    notification = {
                        'type': 'fork',
                        'message': f"{user_info.get('full_name') or user_info.get('email')} forked your playbook '{playbook_info.get('title')}'",
                        'playbook_id': playbook_info.get('id'),
                        'playbook_title': playbook_info.get('title'),
                        'user_id': user_info.get('id'),
                        'user_email': user_info.get('email'),
                        'user_full_name': user_info.get('full_name') or user_info.get('email'),
                        'created_at': fork['forked_at'],
                        'is_read': False
                    }
                    notifications.append(notification)
                    
                except Exception as fork_error:
                    print(f"Error processing fork {fork.get('id')}: {str(fork_error)}")
                    continue
            
            return notifications
        except Exception as e:
            print(f"Error in get_user_notifications: {str(e)}")
            # Return empty list instead of raising exception to prevent API failure
            return []

    async def get_notification_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            # Get playbooks owned by user
            owned_playbooks = await self.get_playbooks_by_user_detailed(user_id, 1000, 0)
            owned_playbook_ids = [p['id'] for p in owned_playbooks]
            
            if not owned_playbook_ids:
                return 0
            
            # Count recent forks (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            response = self.client.table("user_playbooks").select("id", count="exact").in_("original_playbook_id", owned_playbook_ids).gte("forked_at", thirty_days_ago).execute()
            
            return response.count or 0
        except Exception as e:
            print(f"Error getting notification count for user {user_id}: {str(e)}")
            return 0

    async def create_fork_notification(self, original_playbook_id: str, forking_user_id: str, fork_id: str) -> bool:
        """Create a notification for when someone forks a playbook"""
        try:
            # Get forking user details
            forking_user = await self.get_user_by_id(forking_user_id)
            if not forking_user:
                print(f"Could not find forking user {forking_user_id}")
                return False
            
            # Get original playbook details
            original_playbook = await self.get_playbook(original_playbook_id)
            if not original_playbook:
                print(f"Could not find original playbook {original_playbook_id}")
                return False
            
            # Create notification data
            notification_data = {
                "id": str(uuid.uuid4()),
                "type": "fork",
                "playbook_id": original_playbook_id,
                "playbook_title": original_playbook.get('title', 'Unknown Playbook'),
                "user_id": forking_user_id,
                "user_email": forking_user.get('email', 'Unknown User'),
                "user_full_name": forking_user.get('full_name', forking_user.get('email', 'Unknown User')),
                "fork_id": fork_id,
                "message": f"{forking_user.get('full_name', forking_user.get('email'))} forked your playbook '{original_playbook.get('title')}'",
                "created_at": datetime.utcnow().isoformat(),
                "is_read": False
            }
            
            # Try to insert into notifications table if it exists
            try:
                response = self.client.table("notifications").insert(notification_data).execute()
                if response.data:
                    print(f"✅ Created fork notification: {response.data[0]['id']}")
                    return True
            except Exception as table_error:
                print(f"Notifications table not available: {table_error}")
                # Fallback: we'll handle notifications through the existing get_user_notifications method
                return True
            
            return False
        except Exception as e:
            print(f"Error creating fork notification: {str(e)}")
            return False


# Global instance
supabase_service = SupabaseService() 
