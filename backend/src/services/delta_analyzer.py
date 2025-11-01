"""
DeltaAnalyzer service for comparing narrative analyses and generating deltas.

Computes sentiment deltas and theme evolution between two reports for the
same company and persists a `NarrativeDelta` record.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from ..models.narrative_analysis import NarrativeAnalysis
from ..models.narrative_delta import NarrativeDelta, ShiftSignificance
from ..models.financial_report import FinancialReport


class DeltaAnalyzer:
    """Service that compares two reports' analyses and creates a delta."""

    @staticmethod
    def _load_analyses_for_reports(
        db: Session, base_report_id: str, comparison_report_id: str
    ) -> Tuple[NarrativeAnalysis, NarrativeAnalysis, FinancialReport, FinancialReport]:
        """
        Load the latest `NarrativeAnalysis` for each report and their `FinancialReport`s.
        """
        base_report: FinancialReport = (
            db.query(FinancialReport).filter(FinancialReport.id == base_report_id).first()
        )
        comparison_report: FinancialReport = (
            db.query(FinancialReport)
            .filter(FinancialReport.id == comparison_report_id)
            .first()
        )

        if not base_report or not comparison_report:
            raise ValueError("One or both reports not found")

        # Ensure same company and temporal ordering (comparison should be newer)
        if base_report.company_id != comparison_report.company_id:
            raise ValueError("Reports must belong to the same company")

        base_analysis: NarrativeAnalysis = (
            db.query(NarrativeAnalysis)
            .filter(NarrativeAnalysis.report_id == base_report.id)
            .order_by(NarrativeAnalysis.created_at.desc())
            .first()
        )
        comparison_analysis: NarrativeAnalysis = (
            db.query(NarrativeAnalysis)
            .filter(NarrativeAnalysis.report_id == comparison_report.id)
            .order_by(NarrativeAnalysis.created_at.desc())
            .first()
        )

        if not base_analysis or not comparison_analysis:
            raise ValueError("Analyses not found for one or both reports")

        # Optional: enforce temporal constraint if filing_date available
        if (
            comparison_report.filing_date is not None
            and base_report.filing_date is not None
            and comparison_report.filing_date < base_report.filing_date
        ):
            raise ValueError("Comparison report must be more recent than base report")

        return base_analysis, comparison_analysis, base_report, comparison_report

    @staticmethod
    def _compute_theme_evolution(
        base_themes: List[str], comparison_themes: List[str]
    ) -> Tuple[List[str], List[str], Dict[str, float]]:
        """
        Derive added/removed themes; evolved themes are placeholders with 0.0 delta.
        """
        base_set = {t.strip() for t in (base_themes or []) if t and t.strip()}
        comp_set = {t.strip() for t in (comparison_themes or []) if t and t.strip()}

        themes_added = sorted(list(comp_set - base_set))
        themes_removed = sorted(list(base_set - comp_set))
        # Without per-theme intensity, treat overlap as not evolved; keep structure for future
        themes_evolved: Dict[str, float] = {}
        return themes_added, themes_removed, themes_evolved

    @staticmethod
    def compare_reports(
        db: Session, base_report_id: str, comparison_report_id: str
    ) -> NarrativeDelta:
        """
        Compare two report analyses and create/persist a `NarrativeDelta`.
        """
        (
            base_analysis,
            comparison_analysis,
            base_report,
            comparison_report,
        ) = DeltaAnalyzer._load_analyses_for_reports(db, base_report_id, comparison_report_id)

        deltas = comparison_analysis.compare_with_previous(base_analysis)

        themes_added, themes_removed, themes_evolved = DeltaAnalyzer._compute_theme_evolution(
            base_analysis.key_themes or [], comparison_analysis.key_themes or []
        )

        narrative_delta = NarrativeDelta(
            company_id=base_report.company_id,
            base_analysis_id=base_analysis.id,
            comparison_analysis_id=comparison_analysis.id,
            optimism_delta=deltas.get("optimism_delta", 0.0),
            risk_delta=deltas.get("risk_delta", 0.0),
            uncertainty_delta=deltas.get("uncertainty_delta", 0.0),
            overall_sentiment_delta=deltas.get("overall_sentiment_delta", 0.0),
            themes_added=themes_added,
            themes_removed=themes_removed,
            themes_evolved=themes_evolved,
            shift_significance=ShiftSignificance.MINOR,  # will be recalculated below
        )

        # Calculate significance based on combined factors
        narrative_delta.shift_significance = narrative_delta.calculate_significance_level()

        # Upsert: prevent duplicates for same pair
        existing = (
            db.query(NarrativeDelta)
            .filter(
                NarrativeDelta.base_analysis_id == narrative_delta.base_analysis_id,
                NarrativeDelta.comparison_analysis_id == narrative_delta.comparison_analysis_id,
            )
            .first()
        )
        if existing:
            # Update fields on existing record
            existing.optimism_delta = narrative_delta.optimism_delta
            existing.risk_delta = narrative_delta.risk_delta
            existing.uncertainty_delta = narrative_delta.uncertainty_delta
            existing.overall_sentiment_delta = narrative_delta.overall_sentiment_delta
            existing.themes_added = narrative_delta.themes_added
            existing.themes_removed = narrative_delta.themes_removed
            existing.themes_evolved = narrative_delta.themes_evolved
            existing.shift_significance = narrative_delta.shift_significance
            db.add(existing)
            db.flush()
            return existing

        db.add(narrative_delta)
        db.flush()
        return narrative_delta


