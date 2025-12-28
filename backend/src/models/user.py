"""User model for FNA Platform."""

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    """User model for authentication and subscription management."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    subscription_tier = Column(String(50), default="Basic", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    # reports = relationship("FinancialReport", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(email={self.email}, tier={self.subscription_tier})>"
