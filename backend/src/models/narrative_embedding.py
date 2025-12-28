"""NarrativeEmbedding model for FNA Platform."""

from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, ForeignKey, Text, String, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import BaseModel


class SectionType(str, PyEnum):
    """Types of narrative sections."""
    MD_A = "MD_A"
    CEO_LETTER = "CEO_LETTER"
    RISK_FACTORS = "RISK_FACTORS"
    OTHER = "OTHER"


class NarrativeEmbedding(BaseModel):
    """Narrative embedding model for vector search."""
    
    __tablename__ = "narrative_embeddings"
    
    report_id = Column(UUID(as_uuid=True), ForeignKey("financial_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    text_chunk = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False, index=True)
    embedding_vector = Column(JSONB, nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Relationships
    report = relationship("FinancialReport")
    
    def __repr__(self) -> str:
        return f"<NarrativeEmbedding(report_id={self.report_id}, chunk={self.chunk_index})>"
