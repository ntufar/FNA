"""
TrendAnalyzer service for computing historical sentiment trends and timeline metrics.

Calculates rolling and period-over-period trends for optimism, risk, and uncertainty
based on `NarrativeAnalysis` records associated with a company's `FinancialReport`s.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from ..models.narrative_analysis import NarrativeAnalysis
from ..models.financial_report import FinancialReport


@dataclass
class TrendPoint:
    filing_date: Optional[date]
    optimism: Optional[float]
    risk: Optional[float]
    uncertainty: Optional[float]


class TrendAnalyzer:
    """Compute sentiment timelines and trends for a company."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def fetch_company_timeline(self, company_id) -> List[TrendPoint]:
        """
        Load analyses for a company's reports ordered by filing date.
        Returns a list of TrendPoint for charting.
        """
        query = (
            self.db.query(NarrativeAnalysis, FinancialReport)
            .join(FinancialReport, NarrativeAnalysis.report_id == FinancialReport.id)
            .filter(FinancialReport.company_id == company_id)
            .order_by(FinancialReport.filing_date.asc())
        )

        points: List[TrendPoint] = []
        for analysis, report in query.all():
            points.append(
                TrendPoint(
                    filing_date=report.filing_date,
                    optimism=analysis.optimism_score,
                    risk=analysis.risk_score,
                    uncertainty=analysis.uncertainty_score,
                )
            )
        return points

    @staticmethod
    def _delta(current: Optional[float], previous: Optional[float]) -> Optional[float]:
        if current is None or previous is None:
            return None
        return round(current - previous, 4)

    def compute_period_over_period(self, points: List[TrendPoint]) -> List[Dict[str, Any]]:
        """Compute deltas between consecutive points."""
        results: List[Dict[str, Any]] = []
        prev: Optional[TrendPoint] = None
        for p in points:
            results.append(
                {
                    "date": p.filing_date.isoformat() if p.filing_date else None,
                    "optimism": p.optimism,
                    "risk": p.risk,
                    "uncertainty": p.uncertainty,
                    "delta": {
                        "optimism": self._delta(p.optimism, prev.optimism) if prev else None,
                        "risk": self._delta(p.risk, prev.risk) if prev else None,
                        "uncertainty": self._delta(p.uncertainty, prev.uncertainty) if prev else None,
                    },
                }
            )
            prev = p
        return results

    def compute_rolling_average(
        self, points: List[TrendPoint], window: int = 3
    ) -> List[Dict[str, Any]]:
        """Compute rolling average across a sliding window (default 3)."""
        results: List[Dict[str, Any]] = []
        for idx in range(len(points)):
            start = max(0, idx - window + 1)
            window_points = points[start : idx + 1]
            optimism_values = [p.optimism for p in window_points if p.optimism is not None]
            risk_values = [p.risk for p in window_points if p.risk is not None]
            uncertainty_values = [p.uncertainty for p in window_points if p.uncertainty is not None]

            results.append(
                {
                    "date": points[idx].filing_date.isoformat() if points[idx].filing_date else None,
                    "optimism": round(mean(optimism_values), 4) if optimism_values else None,
                    "risk": round(mean(risk_values), 4) if risk_values else None,
                    "uncertainty": round(mean(uncertainty_values), 4) if uncertainty_values else None,
                }
            )
        return results

    def build_trends_payload(self, company_id, window: int = 3) -> Dict[str, Any]:
        """Return a structured payload for the `/companies/{id}/trends` endpoint."""
        timeline = self.fetch_company_timeline(company_id)
        return {
            "timeline": [
                {
                    "date": p.filing_date.isoformat() if p.filing_date else None,
                    "optimism": p.optimism,
                    "risk": p.risk,
                    "uncertainty": p.uncertainty,
                }
                for p in timeline
            ],
            "period_over_period": self.compute_period_over_period(timeline),
            "rolling_average": self.compute_rolling_average(timeline, window=window),
        }


