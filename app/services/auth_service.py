from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.services.supabase_service import supabase_service


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            # Get user from database
            user = await supabase_service.get_user_by_email(email)
            if user:
                # Verify password against hashed password
                if self.verify_password(password, user.get("hashed_password", "")):
                    return {
                        "id": user["id"],
                        "email": user["email"],
                        "full_name": user.get("full_name", ""),
                        "created_at": user.get("created_at", "")
                    }
            return None
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None
    
    async def register_user(self, email: str, password: str, full_name: str) -> Optional[Dict[str, Any]]:
        """Register a new user"""
        try:
            # Hash the password before storing
            hashed_password = self.get_password_hash(password)
            
            # Create user in users table
            user = await supabase_service.create_user(email, password, full_name, hashed_password)
            
            if user:
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "created_at": user["created_at"]
                }
            return None
        except Exception as e:
            raise Exception(f"Failed to register user: {str(e)}")
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        return {"id": user_id, "email": payload.get("email")}


# Global instance
auth_service = AuthService() 
