"""BatchJob model for tracking batch processing jobs.

Stores batch processing job status, progress, and results in PostgreSQL.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class BatchJob(Base):
    """Model for tracking batch processing jobs.
    
    Uses PostgreSQL as the task queue - no external message broker required.
    """
    
    __tablename__ = 'batch_jobs'
    
    # Primary identifier
    batch_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Status tracking
    status = Column(String(50), nullable=False, default='PENDING', index=True)
    
    # Progress tracking
    total_reports = Column(Integer, nullable=False)
    successful = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    
    # Results storage (JSONB for flexibility)
    results = Column(JSON, nullable=True)
    
    # Report IDs for this batch (stored as JSON array)
    report_ids = Column(JSON, nullable=False)
    
    # Timestamps
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="batch_jobs")
    
    def __repr__(self) -> str:
        return f"<BatchJob(batch_id={self.batch_id}, status={self.status}, total={self.total_reports})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert batch job to dictionary."""
        return {
            "batch_id": str(self.batch_id),
            "status": self.status,
            "total_reports": self.total_reports,
            "successful": self.successful,
            "failed": self.failed,
            "results": self.results or [],
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

