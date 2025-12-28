"""NarrativeAnalysis model for FNA Platform."""

from sqlalchemy import Column, Float, ForeignKey, JSON, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class NarrativeAnalysis(BaseModel):
    """Narrative analysis results model."""
    
    __tablename__ = "narrative_analyses"
    
    report_id = Column(UUID(as_uuid=True), ForeignKey("financial_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    optimism_score = Column(Float, nullable=False)
    optimism_confidence = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_confidence = Column(Float, nullable=False)
    uncertainty_score = Column(Float, nullable=False)
    uncertainty_confidence = Column(Float, nullable=False)
    key_themes = Column(JSON, nullable=False, default=list)
    risk_indicators = Column(JSON, nullable=False, default=list)
    narrative_sections = Column(JSON, nullable=False, default=dict)
    financial_metrics = Column(JSON, nullable=True)
    processing_time_seconds = Column(Integer, nullable=False, default=0)
    model_version = Column(String(100), nullable=False)
    
    # Relationships
    report = relationship("FinancialReport", back_populates="analyses")
    
    def __repr__(self) -> str:
        return f"<NarrativeAnalysis(report_id={self.report_id}, sentiment={self.overall_sentiment_score})>"
