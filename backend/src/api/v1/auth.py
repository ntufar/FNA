"""Authentication endpoints for FNA backend API."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from ...core.security import (
    get_current_user,
    create_user_tokens,
    hash_password,
    verify_password
)

router = APIRouter()


# Request/Response models
class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """User registration request model."""
    email: EmailStr
    password: str
    subscription_tier: str = "Basic"


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str
    user: Dict[str, Any]


class UserResponse(BaseModel):
    """User information response model."""
    id: str
    email: str
    subscription_tier: str
    is_active: bool


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT tokens.
    
    This endpoint validates user credentials and returns access/refresh tokens.
    Currently uses mock authentication - TODO: integrate with database.
    """
    # TODO: Replace with actual database user lookup
    # For now, using mock authentication for development
    mock_users = {
        "admin@fna.com": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "admin@fna.com", 
            "password_hash": hash_password("admin123"),
            "subscription_tier": "Enterprise",
            "is_active": True
        },
        "demo@fna.com": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "email": "demo@fna.com",
            "password_hash": hash_password("demo123"), 
            "subscription_tier": "Pro",
            "is_active": True
        }
    }
    
    user = mock_users.get(login_data.email)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create tokens
    user_data = {
        "id": user["id"],
        "email": user["email"], 
        "subscription_tier": user["subscription_tier"]
    }
    
    tokens = create_user_tokens(user_data)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"], 
        token_type=tokens["token_type"],
        user=user_data
    )


@router.post("/register", response_model=TokenResponse)
async def register(register_data: RegisterRequest):
    """Register a new user account.
    
    Currently uses mock registration - TODO: integrate with database.
    """
    # TODO: Replace with actual database user creation
    # For now, mock registration for development
    
    # Validate subscription tier
    valid_tiers = ["Basic", "Pro", "Enterprise"]
    if register_data.subscription_tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription tier"
        )
    
    # Mock user creation
    user_data = {
        "id": "new-user-123",  # Would be generated UUID in real implementation
        "email": register_data.email,
        "subscription_tier": register_data.subscription_tier
    }
    
    tokens = create_user_tokens(user_data)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=user_data
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        subscription_tier=current_user["subscription_tier"], 
        is_active=True  # TODO: Get from database
    )


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout current user.
    
    In a production system, this would invalidate the refresh token.
    For JWT tokens, logout is typically handled client-side by discarding tokens.
    """
    # TODO: Implement token blacklisting or refresh token invalidation
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token.
    
    TODO: Implement refresh token validation and new access token generation.
    """
    # TODO: Validate refresh token and generate new access token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented"
    )
