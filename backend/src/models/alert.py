"""Alert model for FNA Platform."""

from enum import Enum as PyEnum
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class AlertType(str, PyEnum):
    """Types of alerts."""
    SENTIMENT_SHIFT = "SENTIMENT_SHIFT"
    RISK_INCREASE = "RISK_INCREASE"
    THEME_CHANGE = "THEME_CHANGE"


class DeliveryMethod(str, PyEnum):
    """Alert delivery methods."""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"


class Alert(BaseModel):
    """Alert model for notifying users of significant narrative changes."""
    
    __tablename__ = "alerts"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    delta_id = Column(UUID(as_uuid=True), ForeignKey("narrative_deltas.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(30), nullable=False, index=True)
    threshold_percentage = Column(Float, nullable=False)
    actual_change_percentage = Column(Float, nullable=False, default=0.0)
    alert_message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    delivery_method = Column(String(20), nullable=False, default="IN_APP")
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    company = relationship("Company", back_populates="alerts")
    narrative_delta = relationship("NarrativeDelta", back_populates="alerts")
    
    def __repr__(self) -> str:
        return f"<Alert(user_id={self.user_id}, type={self.alert_type}, read={self.is_read})>"
