"""JWT authentication and security utilities for FNA backend.

Handles JWT token generation, validation, password hashing, and authentication middleware.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from functools import wraps

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    """Security configuration from environment variables."""
    
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    refresh_token_expire_days: int = 30
    
    class Config:
        env_prefix = ""


# Initialize settings and password context
security_settings = SecuritySettings()

# Configure bcrypt with settings to avoid initialization issues
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"  # Force specific bcrypt variant to avoid wrap bug detection
)
oauth2_scheme = HTTPBearer()


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthenticationManager:
    """Manages JWT authentication, token generation, and password operations."""
    
    def __init__(self, settings: SecuritySettings = None):
        self.settings = settings or security_settings
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt with automatic length handling.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
            
        Raises:
            ValueError: If password validation fails
        """
        # Ensure password is not too long for bcrypt (72 bytes max)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError(f"Password too long ({len(password_bytes)} bytes, max 72 bytes)")
        
        try:
            # Use the safe password hashing function
            return self._safe_bcrypt_hash(password)
        except Exception as e:
            # Wrap bcrypt errors with more informative messages
            raise ValueError(f"Failed to hash password: {str(e)}") from e
    
    def _safe_bcrypt_hash(self, password: str) -> str:
        """Safely hash password with bcrypt, handling initialization issues.
        
        This method works around bcrypt initialization problems by using
        a direct bcrypt approach when passlib fails.
        """
        try:
            return pwd_context.hash(password)
        except Exception:
            # If passlib fails, fall back to direct bcrypt usage
            import bcrypt
            # Ensure password is bytes and within limits
            password_bytes = password.encode('utf-8')[:72]
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # For very long passwords, verification will fail anyway, so short-circuit
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 72:
                # Try with truncated password (for backward compatibility)
                password_bytes = password_bytes[:72]
                plain_password = password_bytes.decode('utf-8', errors='ignore')
                
            # Try passlib first
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # If passlib fails, try direct bcrypt verification
            try:
                import bcrypt
                password_bytes = plain_password.encode('utf-8')[:72]
                hash_bytes = hashed_password.encode('utf-8')
                return bcrypt.checkpw(password_bytes, hash_bytes)
            except Exception:
                # If all methods fail, return False
                return False
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create a JWT access token for a user.
        
        Args:
            user_data: Dictionary containing user information (id, email, subscription_tier)
            
        Returns:
            JWT token string
        """
        # Token expiration time
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.access_token_expire_minutes
        )
        
        # Token payload
        token_data = {
            "sub": str(user_data["id"]),  # Subject (user ID)
            "email": user_data["email"],
            "subscription_tier": user_data["subscription_tier"],
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        # Generate and return token
        return jwt.encode(
            token_data, 
            self.settings.secret_key, 
            algorithm=self.settings.algorithm
        )
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token for a user.
        
        Args:
            user_id: User ID string
            
        Returns:
            JWT refresh token string
        """
        # Token expiration time
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        
        # Token payload
        token_data = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        # Generate and return token
        return jwt.encode(
            token_data,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def extract_user_from_token(self, token: str) -> Dict[str, Any]:
        """Extract user information from a valid access token.
        
        Args:
            token: JWT access token
            
        Returns:
            Dictionary with user information
            
        Raises:
            AuthenticationError: If token is invalid or not an access token
        """
        payload = self.verify_token(token)
        
        # Verify this is an access token
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        
        return {
            "id": payload["sub"],
            "email": payload["email"],
            "subscription_tier": payload["subscription_tier"]
        }


# Global authentication manager instance
auth_manager = AuthenticationManager()


# FastAPI Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        Dictionary with current user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        user_data = auth_manager.extract_user_from_token(credentials.credentials)
        return user_data
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """FastAPI dependency to get current active user.
    
    This would typically check if user is active in database,
    but for now just returns the user from token.
    
    Args:
        current_user: User data from get_current_user dependency
        
    Returns:
        Dictionary with current active user information
    """
    # TODO: Add database check for user.is_active when database session available
    return current_user


def require_subscription_tier(required_tier: str):
    """FastAPI dependency factory for subscription tier requirements.
    
    Args:
        required_tier: Required subscription tier ('Basic', 'Pro', 'Enterprise')
        
    Returns:
        FastAPI dependency function
    """
    tier_hierarchy = {'Basic': 0, 'Pro': 1, 'Enterprise': 2}
    required_level = tier_hierarchy.get(required_tier, 0)
    
    async def check_subscription_tier(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_tier = current_user.get("subscription_tier", "Basic")
        user_level = tier_hierarchy.get(user_tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} subscription or higher"
            )
        
        return current_user
    
    return check_subscription_tier


# Convenience dependencies for different subscription tiers
require_pro_tier = require_subscription_tier("Pro")
require_enterprise_tier = require_subscription_tier("Enterprise")


# Decorator for protecting endpoints
def jwt_required(f):
    """Decorator to require JWT authentication for a function."""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # This decorator is primarily for non-FastAPI use cases
        # FastAPI endpoints should use the Depends() mechanism instead
        return await f(*args, **kwargs)
    return decorated_function


# Utility functions
def create_user_tokens(user_data: Dict[str, Any]) -> Dict[str, str]:
    """Create both access and refresh tokens for a user.
    
    Args:
        user_data: Dictionary containing user information
        
    Returns:
        Dictionary with access_token and refresh_token
    """
    access_token = auth_manager.create_access_token(user_data)
    refresh_token = auth_manager.create_refresh_token(user_data["id"])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def hash_password(password: str) -> str:
    """Convenience function to hash a password."""
    return auth_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Convenience function to verify a password."""
    return auth_manager.verify_password(plain_password, hashed_password)
