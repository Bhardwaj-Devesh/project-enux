from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.models.auth import UserRegister, UserLogin, UserResponse, UserResponseWithToken, Token
from app.models.profile import ProfileUpdate
from app.services.auth_service import auth_service
from app.services.supabase_service import supabase_service
from app.services.profile_service import profile_service
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponseWithToken)
async def register(user_data: UserRegister):
    """Register a new user and return access token"""
    try:
        # Check if user already exists
        existing_user = await supabase_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        user = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Create profile entry for the new user
        try:
            # Create initial profile data with full name
            profile_data = ProfileUpdate(
                full_name=user_data.full_name
            )
            
            # Create profile in database (username will be extracted from email in service)
            await profile_service.create_or_update_profile(
                user_id=user["id"],
                profile_data=profile_data,
                email=user_data.email
            )
            
        except Exception as profile_error:
            # Log the error but don't fail registration
            print(f"Warning: Failed to create profile for user {user['id']}: {str(profile_error)}")
            # Continue with registration even if profile creation fails
        
        # Create access token for the new user
        access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": user["id"], "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        return UserResponseWithToken(
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                full_name=user["full_name"],
                created_at=user["created_at"]
            ),
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60
        )
    except HTTPException:
        # Re-raise HTTPException as-is to preserve the original error details
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user and return access token"""
    try:
        user = await auth_service.authenticate_user(user_data.email, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": user["id"], "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60
        )
    except HTTPException:
        # Re-raise HTTPException as-is to preserve the original error details
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )





@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    try:
        user = await supabase_service.get_user_by_email(current_user.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user.get("full_name", ""),
            created_at=user["created_at"]
        )
    except HTTPException:
        # Re-raise HTTPException as-is to preserve the original error details
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 
