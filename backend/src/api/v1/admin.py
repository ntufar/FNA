"""
Admin API endpoints for FNA Platform.

Provides administrative functions for user management, subscription management,
and system configuration.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, EmailStr

from ...core.security import get_current_user
from ...database.connection import get_db
from ...models.user import User
from ...models.company import Company

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class UserUpdateRequest(BaseModel):
    """Request model for updating user."""
    email: Optional[EmailStr] = None
    subscription_tier: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    email: str
    subscription_tier: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response model for user list."""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class SubscriptionStatsResponse(BaseModel):
    """Response model for subscription statistics."""
    total_users: int
    basic_tier: int
    pro_tier: int
    enterprise_tier: int
    inactive_users: int


# Helper function to check admin access
async def require_admin_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure user has admin privileges.
    
    Note: This is a placeholder - implement proper admin role checking
    based on your requirements.
    """
    # TODO: Implement proper admin role checking
    # For now, this is a placeholder that requires the user to exist
    # In production, you'd check for an admin role or flag
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subscription_tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    db = Depends(get_db),
    admin: User = Depends(require_admin_access)
):
    """
    List all users with pagination and filtering.
    
    Requires admin access.
    """
    try:
        query = db.query(User)
        
        # Apply filters
        if subscription_tier:
            query = query.filter(User.subscription_tier == subscription_tier)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()
        
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db = Depends(get_db),
    admin: User = Depends(require_admin_access)
):
    """
    Get user details by ID.
    
    Requires admin access.
    """
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse.from_orm(user)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    db = Depends(get_db),
    admin: User = Depends(require_admin_access)
):
    """
    Update user information.
    
    Requires admin access.
    """
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.subscription_tier is not None:
            valid_tiers = ["Basic", "Pro", "Enterprise"]
            if update_data.subscription_tier not in valid_tiers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid subscription tier: {update_data.subscription_tier}. Must be one of: {', '.join(valid_tiers)}"
                )
            user.subscription_tier = update_data.subscription_tier
        if update_data.is_active is not None:
            user.is_active = update_data.is_active
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        return UserResponse.from_orm(user)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db = Depends(get_db),
    admin: User = Depends(require_admin_access)
):
    """
    Delete a user (soft delete by setting is_active=False).
    
    Requires admin access.
    """
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )


@router.get("/stats/subscriptions", response_model=SubscriptionStatsResponse)
async def get_subscription_stats(
    db = Depends(get_db),
    admin: User = Depends(require_admin_access)
):
    """
    Get subscription tier statistics.
    
    Requires admin access.
    """
    try:
        total_users = db.query(User).count()
        basic_tier = db.query(User).filter(User.subscription_tier == "Basic").count()
        pro_tier = db.query(User).filter(User.subscription_tier == "Pro").count()
        enterprise_tier = db.query(User).filter(User.subscription_tier == "Enterprise").count()
        inactive_users = db.query(User).filter(User.is_active == False).count()
        
        return SubscriptionStatsResponse(
            total_users=total_users,
            basic_tier=basic_tier,
            pro_tier=pro_tier,
            enterprise_tier=enterprise_tier,
            inactive_users=inactive_users
        )
    except Exception as e:
        logger.error(f"Error getting subscription stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription statistics"
        )


@router.get("/companies", response_model=List[dict])
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db = Depends(get_db),
    admin: User = Depends(require_admin_access)
):
    """
    List all companies in the system.
    
    Requires admin access.
    """
    try:
        offset = (page - 1) * page_size
        companies = db.query(Company).offset(offset).limit(page_size).all()
        
        return [
            {
                "id": str(company.id),
                "ticker_symbol": company.ticker_symbol,
                "company_name": company.company_name,
                "sector": company.sector,
                "industry": company.industry,
                "created_at": company.created_at.isoformat() if company.created_at else None
            }
            for company in companies
        ]
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list companies"
        )

