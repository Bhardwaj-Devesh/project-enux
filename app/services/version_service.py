"""
Version Management Service
Handles playbook versioning, file versioning, and version-aware operations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.services.supabase_service import supabase_service


class VersionService:
    """Service for managing playbook versions"""
    
    def __init__(self):
        """Initialize version service"""
        pass
    
    async def get_current_version(self, playbook_id: str) -> int:
        """Get current version number for a playbook"""
        try:
            playbook = await supabase_service.get_playbook(playbook_id)
            if not playbook:
                raise Exception(f"Playbook {playbook_id} not found")
            return playbook.get('latest_version', 1)
        except Exception as e:
            raise Exception(f"Failed to get current version: {str(e)}")
    
    async def increment_version(self, playbook_id: str, user_id: str) -> int:
        """Increment version when playbook is updated"""
        try:
            current_version = await self.get_current_version(playbook_id)
            new_version = current_version + 1
            
            # Update playbook version
            update_data = {
                'latest_version': new_version,
                'version': f'v{new_version}',
                'updated_at': datetime.utcnow().isoformat()
            }
            
            updated_playbook = await supabase_service.update_playbook(playbook_id, update_data)
            if not updated_playbook:
                raise Exception("Failed to update playbook version")
            
            return new_version
        except Exception as e:
            raise Exception(f"Failed to increment version: {str(e)}")
    
    async def get_version_files(self, playbook_id: str, version_number: int) -> List[Dict[str, Any]]:
        """Get files for a specific version of a playbook"""
        try:
            # Use the database function to get files for specific version
            response = supabase_service.client.rpc(
                'get_playbook_files_for_version',
                {'p_playbook_id': playbook_id, 'p_version': version_number}
            ).execute()
            
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to get version files: {str(e)}")
    
    async def get_user_playbook_version_files(self, user_playbook_id: str, version_number: int) -> List[Dict[str, Any]]:
        """Get files for a specific version of a user playbook (fork)"""
        try:
            # Use the database function to get files for specific version
            response = supabase_service.client.rpc(
                'get_user_playbook_files_for_version',
                {'p_user_playbook_id': user_playbook_id, 'p_version': version_number}
            ).execute()
            
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to get user playbook version files: {str(e)}")
    
    async def mark_files_inactive(self, playbook_id: str, file_names: List[str], new_version: int):
        """Mark existing files as inactive when updating playbook"""
        try:
            # Get current active files
            current_files = await supabase_service.get_playbook_files(playbook_id)
            
            # Mark files as inactive if they're being updated
            for file_record in current_files:
                if file_record['file_name'] in file_names:
                    update_data = {
                        'is_active': False,
                        'last_modified_at': datetime.utcnow().isoformat()
                    }
                    await supabase_service.update_playbook_file(file_record['id'], update_data)
        except Exception as e:
            raise Exception(f"Failed to mark files inactive: {str(e)}")
    
    async def create_file_with_version(self, playbook_id: str, file_data: Dict[str, Any], version_number: int) -> Dict[str, Any]:
        """Create a new file entry with version tracking"""
        try:
            file_data.update({
                'playbook_id': playbook_id,
                'version_created': version_number,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat(),
                'last_modified_at': datetime.utcnow().isoformat()
            })
            
            return await supabase_service.create_playbook_file(file_data)
        except Exception as e:
            raise Exception(f"Failed to create file with version: {str(e)}")
    
    async def create_user_playbook_file_with_version(self, user_playbook_id: str, file_data: Dict[str, Any], version_number: int) -> Dict[str, Any]:
        """Create a new user playbook file entry with version tracking"""
        try:
            file_data.update({
                'user_playbook_id': user_playbook_id,
                'version_created': version_number,
                'is_active': True,
                'uploaded_at': datetime.utcnow().isoformat(),
                'last_modified_at': datetime.utcnow().isoformat()
            })
            
            return await supabase_service.create_user_playbook_file(file_data)
        except Exception as e:
            raise Exception(f"Failed to create user playbook file with version: {str(e)}")
    
    async def get_latest_version_for_fork(self, playbook_id: str) -> int:
        """Get the latest version number for forking"""
        try:
            return await self.get_current_version(playbook_id)
        except Exception as e:
            raise Exception(f"Failed to get latest version for fork: {str(e)}")
    
    async def validate_version_exists(self, playbook_id: str, version_number: int) -> bool:
        """Validate that a specific version exists for a playbook"""
        try:
            current_version = await self.get_current_version(playbook_id)
            return 1 <= version_number <= current_version
        except Exception as e:
            raise Exception(f"Failed to validate version: {str(e)}")


# Global instance
version_service = VersionService()
