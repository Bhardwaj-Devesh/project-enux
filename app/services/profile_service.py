from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.supabase_service import supabase_service
from app.models.profile import ProfileUpdate, ProfileResponse
import logging

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self):
        self.supabase = supabase_service

    async def get_profile(self, user_id: str) -> Optional[ProfileResponse]:
        """Get user profile by user ID"""
        try:
            response = self.supabase.client.table("profiles").select("*").eq("id", user_id).execute()
            
            if not response.data:
                return None
            
            profile_data = response.data[0]
            return ProfileResponse(**profile_data)
        except Exception as e:
            logger.error(f"Error fetching profile for user {user_id}: {str(e)}")
            raise

    async def create_or_update_profile(self, user_id: str, profile_data: ProfileUpdate, email: str) -> ProfileResponse:
        """Create or update user profile"""
        try:
            # Check if profile exists
            existing_profile = await self.get_profile(user_id)
            
            # Prepare data for database
            update_data = profile_data.dict(exclude_unset=True)
            
            # Convert website URL to string if present
            if update_data.get('website'):
                update_data['website'] = str(update_data['website'])
            
            if existing_profile:
                # Update existing profile
                update_data['updated_at'] = datetime.utcnow().isoformat()
                
                response = self.supabase.client.table("profiles").update(update_data).eq("id", user_id).execute()
                
                if not response.data:
                    raise Exception("Failed to update profile")
                
                return ProfileResponse(**response.data[0])
            else:
                # Create new profile
                username = email.split('@')[0] if '@' in email else user_id
                
                new_profile_data = {
                    "id": user_id,
                    "username": username,
                    **update_data,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                response = self.supabase.client.table("profiles").insert(new_profile_data).execute()
                
                if not response.data:
                    raise Exception("Failed to create profile")
                
                return ProfileResponse(**response.data[0])
        except Exception as e:
            logger.error(f"Error creating/updating profile for user {user_id}: {str(e)}")
            raise

    async def update_avatar_url(self, user_id: str, avatar_url: str) -> bool:
        """Update user's avatar URL"""
        try:
            response = self.supabase.client.table("profiles").update({
                "avatar_url": avatar_url,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating avatar URL for user {user_id}: {str(e)}")
            raise

    async def get_profiles_by_stage(self, stage: str, limit: int = 10) -> List[ProfileResponse]:
        """Get profiles by career stage"""
        try:
            response = self.supabase.client.table("profiles").select("*").eq("stage", stage).limit(limit).execute()
            
            profiles = []
            for profile_data in response.data:
                profiles.append(ProfileResponse(**profile_data))
            
            return profiles
        except Exception as e:
            logger.error(f"Error fetching profiles by stage {stage}: {str(e)}")
            raise

    async def search_profiles(self, query: str, limit: int = 10) -> List[ProfileResponse]:
        """Search profiles by name, bio, or interests"""
        try:
            # Search in full_name, bio, and interests
            response = self.supabase.client.table("profiles").select("*").or_(
                f"full_name.ilike.%{query}%,bio.ilike.%{query}%"
            ).limit(limit).execute()
            
            profiles = []
            for profile_data in response.data:
                profiles.append(ProfileResponse(**profile_data))
            
            return profiles
        except Exception as e:
            logger.error(f"Error searching profiles with query '{query}': {str(e)}")
            raise

    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile (for account deletion)"""
        try:
            response = self.supabase.client.table("profiles").delete().eq("id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting profile for user {user_id}: {str(e)}")
            raise


# Create singleton instance
profile_service = ProfileService()
