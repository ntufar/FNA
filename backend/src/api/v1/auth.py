"""Authentication endpoints for FNA backend API."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from ...core.security import (
    get_current_user,
    create_user_tokens,
    hash_password,
    verify_password
)
from ...database.connection import get_db
from ...models.user import User

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
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('subscription_tier')
    def validate_subscription_tier(cls, v):
        valid_tiers = ["Basic", "Pro", "Enterprise"]
        if v not in valid_tiers:
            raise ValueError(f'Subscription tier must be one of: {", ".join(valid_tiers)}')
        return v


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
    last_login: str = None
    created_at: str


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens.
    
    This endpoint validates user credentials against the database and returns access/refresh tokens.
    """
    # Look up user in database
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create tokens
    user_data = {
        "id": str(user.id),
        "email": user.email, 
        "subscription_tier": user.subscription_tier
    }
    
    tokens = create_user_tokens(user_data)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"], 
        token_type=tokens["token_type"],
        user=user_data
    )


@router.post("/register", response_model=TokenResponse)
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account.
    
    Creates a new user in the database with hashed password and returns authentication tokens.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == register_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        email=register_data.email,
        password_hash=hash_password(register_data.password),
        subscription_tier=register_data.subscription_tier,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )
    
    # Create tokens for the new user
    user_data = {
        "id": str(new_user.id),
        "email": new_user.email,
        "subscription_tier": new_user.subscription_tier
    }
    
    tokens = create_user_tokens(user_data)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=user_data
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information from database."""
    # Fetch full user data from database
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        subscription_tier=user.subscription_tier,
        is_active=user.is_active,
        last_login=user.last_login.isoformat() if user.last_login else None,
        created_at=user.created_at.isoformat()
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
