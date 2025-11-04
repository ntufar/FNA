"""FNA backend models package.

This package contains all SQLAlchemy ORM models for the Financial Narrative Analyzer.
"""

from .base import Base, BaseModel, TimestampMixin, UUIDMixin
from .user import User
from .company import Company
from .financial_report import FinancialReport, ReportType, FileFormat, DownloadSource, ProcessingStatus
from .narrative_analysis import NarrativeAnalysis
from .narrative_embedding import NarrativeEmbedding, SectionType
from .narrative_delta import NarrativeDelta, ShiftSignificance
from .alert import Alert, AlertType, DeliveryMethod
from .batch_job import BatchJob

# Export all models for easy imports
__all__ = [
    "Base",
    "BaseModel", 
    "TimestampMixin",
    "UUIDMixin",
    "User",
    "Company",
    "FinancialReport",
    "ReportType",
    "FileFormat", 
    "DownloadSource",
    "ProcessingStatus",
    "NarrativeAnalysis",
    "NarrativeEmbedding",
    "SectionType",
    "NarrativeDelta",
    "ShiftSignificance",
    "Alert",
    "AlertType",
    "DeliveryMethod",
    "BatchJob",
]
