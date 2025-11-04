"""
NarrativeDelta model for FNA backend.

Represents comparison analysis between two narrative analyses, tracking sentiment changes
and theme evolution over time for the same company.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy import Column, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base
import enum


class ShiftSignificance(enum.Enum):
    """Enumeration of narrative change significance levels."""
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class NarrativeDelta(Base):
    """
    Narrative delta model representing comparison between two analyses.
    
    Tracks sentiment changes, theme evolution, and shift significance when comparing
    financial reports from the same company across different time periods.
    """
    
    __tablename__ = 'narrative_deltas'
    
    # Foreign key relationships
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False, index=True)
    base_analysis_id = Column(UUID(as_uuid=True), ForeignKey('narrative_analyses.id'), nullable=False, index=True)
    comparison_analysis_id = Column(UUID(as_uuid=True), ForeignKey('narrative_analyses.id'), nullable=False, index=True)
    
    # Sentiment delta scores (-1.0 to 1.0, positive = increase)
    optimism_delta = Column(Float, nullable=False)
    risk_delta = Column(Float, nullable=False)
    uncertainty_delta = Column(Float, nullable=False)
    overall_sentiment_delta = Column(Float, nullable=False)
    
    # Theme evolution tracking
    themes_added = Column(JSON, nullable=False, default=list)  # New themes in comparison report
    themes_removed = Column(JSON, nullable=False, default=list)  # Themes absent in comparison report
    themes_evolved = Column(JSON, nullable=False, default=dict)  # Themes with emphasis changes
    
    # Change significance classification
    shift_significance = Column(SQLEnum(ShiftSignificance), nullable=False, index=True)
    
    # Relationships
    company = relationship("Company")
    base_analysis = relationship("NarrativeAnalysis", foreign_keys=[base_analysis_id])
    comparison_analysis = relationship("NarrativeAnalysis", foreign_keys=[comparison_analysis_id])
    alerts = relationship("Alert", back_populates="narrative_delta", cascade="all, delete-orphan")
    
    @property
    def absolute_sentiment_change(self) -> float:
        """Calculate the absolute magnitude of overall sentiment change."""
        return abs(self.overall_sentiment_delta)
    
    @property
    def is_positive_change(self) -> bool:
        """Check if overall sentiment change is positive."""
        return self.overall_sentiment_delta > 0
    
    @property
    def is_negative_change(self) -> bool:
        """Check if overall sentiment change is negative."""
        return self.overall_sentiment_delta < 0
    
    def is_significant_change(self, threshold: float = 0.15) -> bool:
        """Check if sentiment change exceeds significance threshold (default 15%)."""
        return self.absolute_sentiment_change >= threshold
    
    @property
    def added_themes_count(self) -> int:
        """Get count of newly added themes."""
        return len(self.themes_added) if self.themes_added else 0
    
    @property
    def removed_themes_count(self) -> int:
        """Get count of removed themes."""
        return len(self.themes_removed) if self.themes_removed else 0
    
    @property
    def evolved_themes_count(self) -> int:
        """Get count of themes with changed emphasis."""
        return len(self.themes_evolved) if self.themes_evolved else 0
    
    @property
    def total_theme_changes(self) -> int:
        """Get total number of theme changes."""
        return self.added_themes_count + self.removed_themes_count + self.evolved_themes_count
    
    @property
    def risk_increase_percentage(self) -> float:
        """Calculate risk increase as percentage (0 to 100)."""
        return round(self.risk_delta * 100, 2)
    
    @property
    def optimism_change_percentage(self) -> float:
        """Calculate optimism change as percentage (-100 to 100)."""
        return round(self.optimism_delta * 100, 2)
    
    @property
    def uncertainty_change_percentage(self) -> float:
        """Calculate uncertainty change as percentage (-100 to 100)."""
        return round(self.uncertainty_delta * 100, 2)
    
    def validate_delta_scores(self) -> bool:
        """
        Validate that delta scores are within valid range (-1.0 to 1.0).
        
        Returns:
            bool: True if all delta scores are valid
        """
        deltas = [
            self.optimism_delta,
            self.risk_delta, 
            self.uncertainty_delta,
            self.overall_sentiment_delta
        ]
        
        return all(-1.0 <= delta <= 1.0 for delta in deltas)
    
    def calculate_significance_level(self) -> ShiftSignificance:
        """
        Calculate shift significance based on magnitude of changes.
        
        Returns:
            ShiftSignificance: Calculated significance level
        """
        # Weighted scoring considering sentiment change and theme evolution
        sentiment_weight = self.absolute_sentiment_change * 2  # 0.0 to 2.0
        theme_weight = min(self.total_theme_changes / 10, 1.0)  # 0.0 to 1.0, capped
        
        combined_score = (sentiment_weight + theme_weight) / 3  # 0.0 to 1.0
        
        if combined_score >= 0.8:
            return ShiftSignificance.CRITICAL
        elif combined_score >= 0.5:
            return ShiftSignificance.MAJOR
        elif combined_score >= 0.2:
            return ShiftSignificance.MODERATE
        else:
            return ShiftSignificance.MINOR
    
    def get_sentiment_change_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of sentiment changes.
        
        Returns:
            dict: Summary of all sentiment changes with interpretations
        """
        return {
            'overall_change': {
                'delta': self.overall_sentiment_delta,
                'percentage': round(self.overall_sentiment_delta * 100, 2),
                'direction': 'positive' if self.is_positive_change else 'negative' if self.is_negative_change else 'neutral',
                'magnitude': 'significant' if self.is_significant_change() else 'minor'
            },
            'dimensional_changes': {
                'optimism': {
                    'delta': self.optimism_delta,
                    'percentage': self.optimism_change_percentage
                },
                'risk': {
                    'delta': self.risk_delta,
                    'percentage': self.risk_increase_percentage
                },
                'uncertainty': {
                    'delta': self.uncertainty_delta,
                    'percentage': self.uncertainty_change_percentage
                }
            },
            'theme_evolution': {
                'added_count': self.added_themes_count,
                'removed_count': self.removed_themes_count,
                'evolved_count': self.evolved_themes_count,
                'total_changes': self.total_theme_changes
            },
            'significance': {
                'level': self.shift_significance.value if self.shift_significance else 'unknown',
                'calculated_level': self.calculate_significance_level().value
            }
        }
    
    def get_theme_changes_by_type(self) -> Dict[str, List[str]]:
        """
        Get theme changes organized by change type.
        
        Returns:
            dict: Theme changes categorized by type
        """
        return {
            'added_themes': list(self.themes_added) if self.themes_added else [],
            'removed_themes': list(self.themes_removed) if self.themes_removed else [],
            'evolved_themes': list(self.themes_evolved.keys()) if self.themes_evolved else []
        }
    
    def should_trigger_alert(self, user_thresholds: Dict[str, float]) -> bool:
        """
        Check if this delta should trigger user alerts based on thresholds.
        
        Args:
            user_thresholds: Dict with threshold values for different metrics
            
        Returns:
            bool: True if any threshold is exceeded
        """
        # Check sentiment change thresholds
        sentiment_threshold = user_thresholds.get('sentiment_change', 0.2)  # 20% default
        if self.absolute_sentiment_change >= sentiment_threshold:
            return True
        
        # Check risk increase threshold
        risk_threshold = user_thresholds.get('risk_increase', 0.15)  # 15% default
        if self.risk_delta >= risk_threshold:
            return True
        
        # Check theme change threshold
        theme_threshold = user_thresholds.get('theme_changes', 5)  # 5 changes default
        if self.total_theme_changes >= theme_threshold:
            return True
        
        # Check significance level threshold
        significance_levels = {
            ShiftSignificance.MINOR: 1,
            ShiftSignificance.MODERATE: 2,
            ShiftSignificance.MAJOR: 3,
            ShiftSignificance.CRITICAL: 4
        }
        
        min_significance = user_thresholds.get('min_significance', 3)  # MAJOR default
        current_significance = significance_levels.get(self.shift_significance, 1)
        
        return current_significance >= min_significance
    
    def get_alert_messages(self) -> List[str]:
        """
        Generate human-readable alert messages for significant changes.
        
        Returns:
            list: Alert messages for different types of changes
        """
        messages = []
        
        # Sentiment change alerts
        if self.is_significant_change():
            direction = "increased" if self.is_positive_change else "decreased"
            percentage = abs(round(self.overall_sentiment_delta * 100, 1))
            messages.append(f"Overall sentiment {direction} by {percentage}%")
        
        # Risk increase alerts
        if self.risk_delta >= 0.1:  # 10% increase
            messages.append(f"Risk perception increased by {self.risk_increase_percentage}%")
        
        # Theme change alerts
        if self.total_theme_changes >= 3:
            messages.append(f"{self.total_theme_changes} theme changes detected")
        
        # Significance level alerts
        if self.shift_significance in [ShiftSignificance.MAJOR, ShiftSignificance.CRITICAL]:
            messages.append(f"{self.shift_significance.value.lower()} narrative shift identified")
        
        return messages
    
    def __repr__(self) -> str:
        """String representation of NarrativeDelta."""
        return (
            f"<NarrativeDelta("
            f"company_id={str(self.company_id)[:8]}..., "
            f"sentiment_delta={self.overall_sentiment_delta:.3f}, "
            f"theme_changes={self.total_theme_changes}, "
            f"significance={self.shift_significance.value if self.shift_significance else 'None'}"
            f")>"
        )
