"""API key authentication for programmatic access to FNA API.

Provides API key-based authentication as an alternative to JWT tokens
for enterprise integrations and batch processing.
"""

import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Depends, Header
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.user import User


class APIKeyAuth:
    """Manages API key generation, validation, and authentication."""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure random API key.
        
        Returns:
            A 32-character hexadecimal API key string
        """
        # Generate 32 bytes of random data and convert to hex (64 chars)
        # Then take first 32 characters for a shorter key
        random_bytes = secrets.token_bytes(32)
        api_key = secrets.token_urlsafe(32)  # 43 characters, URL-safe
        return api_key[:32]  # Use first 32 characters
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for secure storage.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            SHA-256 hash of the API key
        """
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_api_key(provided_key: str, stored_hash: str) -> bool:
        """Verify an API key against its stored hash.
        
        Args:
            provided_key: API key provided by client
            stored_hash: Hashed API key stored in database
            
        Returns:
            True if key matches, False otherwise
        """
        provided_hash = APIKeyAuth.hash_api_key(provided_key)
        return secrets.compare_digest(provided_hash, stored_hash)


async def get_api_key_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """FastAPI dependency to authenticate user via API key.
    
    This dependency can be used as an alternative to JWT authentication
    for programmatic API access. Supports both X-API-Key header and 
    Authorization: Bearer <api_key> format.
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session
        
    Returns:
        Dictionary with user information if authenticated, None otherwise
        
    Raises:
        HTTPException: If API key is invalid or user is inactive
    """
    # If no API key provided, return None (allows endpoint to use JWT as fallback)
    if not x_api_key:
        return None
    
    # Try to find user by API key hash
    api_key_hash = APIKeyAuth.hash_api_key(x_api_key)
    user = db.query(User).filter(User.api_key_hash == api_key_hash).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Check if user has API access based on subscription tier
    if not user.can_access_api():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API access requires Pro or Enterprise subscription"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "subscription_tier": user.subscription_tier
    }


async def get_current_user_or_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """FastAPI dependency that accepts either JWT token or API key.
    
    Tries API key authentication first, then falls back to JWT.
    This allows endpoints to support both authentication methods.
    
    Args:
        x_api_key: API key from X-API-Key header
        authorization: Authorization header (may contain Bearer token or API key)
        db: Database session
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # Try API key from X-API-Key header
    if x_api_key:
        api_user = await get_api_key_user(x_api_key, db)
        if api_user:
            return api_user
    
    # Try API key from Authorization header (Bearer <api_key> format)
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "", 1)
        # Try as API key first (if it's not a JWT, it might be an API key)
        if len(api_key) > 50:  # JWT tokens are typically longer
            # Likely a JWT token, skip API key check
            pass
        else:
            try:
                api_user = await get_api_key_user(api_key, db)
                if api_user:
                    return api_user
            except HTTPException:
                # If API key auth fails, fall through to JWT auth
                pass
    
    # Fall back to JWT authentication
    from ..core.security import get_current_user, oauth2_scheme
    from fastapi.security import HTTPAuthorizationCredentials
    
    try:
        # Extract Bearer token from Authorization header
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "", 1)
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            return await get_current_user(credentials)
    except Exception:
        pass
    
    # If all authentication methods fail
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either JWT token or API key.",
        headers={"WWW-Authenticate": "Bearer, ApiKey"}
    )


def require_api_access(
    current_user: Dict[str, Any] = Depends(get_current_user_or_api_key)
) -> Dict[str, Any]:
    """FastAPI dependency to ensure user has API access.
    
    Args:
        current_user: User data from authentication
        
    Returns:
        User data if access is granted
        
    Raises:
        HTTPException: If user doesn't have API access
    """
    subscription_tier = current_user.get("subscription_tier", "Basic")
    if subscription_tier not in ["Pro", "Enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API access requires Pro or Enterprise subscription"
        )
    
    return current_user

