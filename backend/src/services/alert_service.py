"""
AlertService for creating and managing user alerts based on NarrativeDelta metrics.
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from ..models.alert import Alert, AlertType
from ..models.narrative_delta import NarrativeDelta


class AlertService:
    """Service to create alerts when thresholds are exceeded."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_sentiment_shift_if_needed(
        self,
        user_id: str,
        company_id: str,
        delta: NarrativeDelta,
        threshold_percentage: float,
    ) -> Optional[Alert]:
        change_pct = abs(delta.overall_sentiment_delta * 100.0) if delta.overall_sentiment_delta is not None else 0.0
        if change_pct >= threshold_percentage:
            alert = Alert.create_sentiment_shift_alert(
                user_id=user_id,
                company_id=company_id,
                delta_id=str(delta.id),
                threshold=threshold_percentage,
                actual_change=change_pct,
                direction="increase" if (delta.overall_sentiment_delta or 0) >= 0 else "decrease",
            )
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            return alert
        return None


