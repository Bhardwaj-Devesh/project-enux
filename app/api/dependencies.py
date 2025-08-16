from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth_service import auth_service
from app.models.auth import TokenData


# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        user_data = auth_service.get_current_user(token)
        
        if user_data is None:
            raise credentials_exception
        
        return TokenData(user_id=user_data["id"], email=user_data["email"])
    except Exception:
        raise credentials_exception


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[TokenData]:
    """Get current user if token is provided, otherwise return None"""
    try:
        if credentials is None:
            return None
        
        token = credentials.credentials
        user_data = auth_service.get_current_user(token)
        
        if user_data is None:
            return None
        
        return TokenData(user_id=user_data["id"], email=user_data["email"])
    except Exception:
        return None


async def get_authenticated_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get authenticated user - required for protected endpoints"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        user_data = auth_service.get_current_user(token)
        
        if user_data is None:
            raise credentials_exception
        
        return TokenData(user_id=user_data["id"], email=user_data["email"])
    except Exception:
        raise credentials_exception 
