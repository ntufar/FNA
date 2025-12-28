"""Company model for FNA Platform."""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class Company(BaseModel):
    """Company model for entities being analyzed."""
    
    __tablename__ = "companies"
    
    ticker_symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True, index=True)
    industry = Column(String(100), nullable=True, index=True)
    
    # Relationships
    reports = relationship("FinancialReport", back_populates="company", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="company", cascade="all, delete-orphan")
    
    @property
    def latest_report(self):
        """Get the most recently filed report for this company."""
        if not self.reports:
            return None
        # Sort by filing_date descending and return the first one
        return sorted(self.reports, key=lambda r: r.filing_date, reverse=True)[0]
    
    @property
    def reports_count(self) -> int:
        """Get the total number of reports for this company."""
        return len(self.reports)
    
    def __repr__(self) -> str:
        return f"<Company(ticker={self.ticker_symbol}, name={self.company_name})>"
