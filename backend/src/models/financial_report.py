"""FinancialReport model for FNA Platform."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, ForeignKey, Date, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class ReportType(str, PyEnum):
    """Types of financial reports."""
    TEN_K = "10-K"
    TEN_Q = "10-Q"
    EIGHT_K = "8-K"
    ANNUAL = "Annual"
    OTHER = "Other"


class FileFormat(str, PyEnum):
    """File formats for reports."""
    PDF = "PDF"
    HTML = "HTML"
    TXT = "TXT"
    IXBRL = "iXBRL"


class DownloadSource(str, PyEnum):
    """Sources of report downloads."""
    SEC_AUTO = "SEC_AUTO"
    MANUAL_UPLOAD = "MANUAL_UPLOAD"


class ProcessingStatus(str, PyEnum):
    """Processing status for reports."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FinancialReport(BaseModel):
    """Financial report model."""
    
    __tablename__ = "financial_reports"
    
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(20), nullable=False, index=True)
    fiscal_period = Column(String(20), nullable=False)
    filing_date = Column(Date, nullable=False, index=True)
    report_url = Column(String(500), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_format = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    download_source = Column(String(20), nullable=False)
    processing_status = Column(String(20), default="PENDING", nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="reports")
    analyses = relationship("NarrativeAnalysis", back_populates="report", cascade="all, delete-orphan")
    
    def reset_to_pending(self) -> None:
        """Reset report processing status to pending."""
        self.processing_status = ProcessingStatus.PENDING
        self.processed_at = None

    @property
    def is_completed(self) -> bool:
        """Check if report has been successfully processed."""
        return self.processing_status == ProcessingStatus.COMPLETED

    @property
    def latest_analysis(self) -> Optional['NarrativeAnalysis']:
        """Get the most recent narrative analysis for this report."""
        if not self.analyses:
            return None
        return sorted(self.analyses, key=lambda x: x.created_at, reverse=True)[0]

    def set_processing(self) -> None:
        """Set report status to PROCESSING."""
        self.processing_status = ProcessingStatus.PROCESSING
    
    def set_completed(self) -> None:
        """Set report status to COMPLETED and update timestamp."""
        self.processing_status = ProcessingStatus.COMPLETED
        self.processed_at = datetime.now(timezone.utc)
    
    def set_failed(self) -> None:
        """Set report status to FAILED."""
        self.processing_status = ProcessingStatus.FAILED

    def validate_file_size(self, max_size_bytes: int = 52428800) -> bool:
        """Validate report file size."""
        return self.file_size_bytes <= max_size_bytes

    def validate_fiscal_period(self) -> bool:
        """Basic validation of fiscal period format (e.g., 'FY 2024', 'Q1 2024')."""
        if not self.fiscal_period:
            return False
        import re
        return bool(re.match(r'^(FY|Q[1-4])\s\d{4}$', self.fiscal_period))
    
    def __repr__(self) -> str:
        return f"<FinancialReport(id={self.id}, type={self.report_type}, period={self.fiscal_period})>"
