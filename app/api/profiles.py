from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List
from app.models.profile import ProfileUpdate, ProfileResponse, AvatarUploadResponse
from app.models.auth import TokenData
from app.api.dependencies import get_authenticated_user
from app.services.profile_service import profile_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_user: TokenData = Depends(get_authenticated_user)):
    """Get current user's profile"""
    try:
        profile = await profile_service.get_profile(current_user.user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found for user"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Update current user's profile. Creates a new profile if one doesn't exist.
    
    The user_id and username are automatically fetched from the authentication token.
    The payload should only contain profile fields like full_name, bio, company, etc.
    """
    try:
        # user_id and username are automatically fetched from the auth token
        # No need to include them in the payload
        profile = await profile_service.create_or_update_profile(
            current_user.user_id, 
            profile_data, 
            current_user.email or ""
        )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/me/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Upload profile picture for the user"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only images are allowed"
            )
        
        # Validate file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum limit of 5MB"
            )
        
        # For now, we'll use a placeholder URL
        # In a real implementation, you would upload to a storage service
        # like AWS S3, Google Cloud Storage, or Supabase Storage
        avatar_url = f"https://storage.example.com/avatars/{current_user.user_id}.jpg"
        
        # Update profile with new avatar URL
        success = await profile_service.update_avatar_url(current_user.user_id, avatar_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update avatar URL"
            )
        
        return AvatarUploadResponse(
            avatar_url=avatar_url,
            message="Avatar uploaded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Optional endpoints for future features
@router.get("/search", response_model=List[ProfileResponse])
async def search_profiles(
    query: str,
    limit: int = 10,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Search profiles by name, bio, or interests"""
    try:
        if len(query) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters long"
            )
        
        profiles = await profile_service.search_profiles(query, limit)
        return profiles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stage/{stage}", response_model=List[ProfileResponse])
async def get_profiles_by_stage(
    stage: str,
    limit: int = 10,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get profiles by career stage"""
    try:
        valid_stages = ['student', 'junior', 'mid-level', 'senior', 'lead', 'manager', 'architect', 'other']
        if stage not in valid_stages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
            )
        
        profiles = await profile_service.get_profiles_by_stage(stage, limit)
        return profiles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profiles by stage {stage}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
