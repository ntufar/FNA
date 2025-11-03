"""Analysis endpoints for FNA backend API."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.security import get_current_user, require_enterprise_tier
from ...database.connection import get_db
from ...services.delta_analyzer import DeltaAnalyzer
from ...models.narrative_delta import NarrativeDelta
from ...models.narrative_analysis import NarrativeAnalysis as NA
from ...models.financial_report import FinancialReport

router = APIRouter()


# Request/Response models
class AnalysisResponse(BaseModel):
    """Analysis results response model (aligned with frontend)."""
    id: str
    report_id: str
    optimism_score: float
    optimism_confidence: float
    risk_score: float 
    risk_confidence: float
    uncertainty_score: float
    uncertainty_confidence: float
    key_themes: List[Any] = []
    risk_indicators: List[Any] = []
    narrative_sections: Dict[str, Any] = {}
    financial_metrics: Dict[str, Any] | None = None
    processing_time_seconds: int | None = None
    model_version: str
    created_at: str
    # Optional embedded report summary for labeling in UI
    report: Dict[str, Any] | None = None


class ComparisonRequest(BaseModel):
    """Report comparison request model."""
    base_report_id: str
    comparison_report_id: str


class ComparisonResponse(BaseModel):
    """Report comparison response model."""
    id: str
    base_analysis_id: str
    comparison_analysis_id: str
    optimism_delta: float
    risk_delta: float
    uncertainty_delta: float
    overall_sentiment_delta: float
    significant_changes: List[str]
    delta_summary: str


class SimilaritySearchRequest(BaseModel):
    """Similarity search request model."""
    query_text: str
    company_id: str = None
    limit: int = 10


def _to_response(analysis: NA, report: FinancialReport | None) -> AnalysisResponse:
    report_dict = None
    if report:
        report_dict = {
            "id": str(report.id),
            "company_id": str(report.company_id),
            "company_name": report.company.company_name if report.company else None,
            "ticker_symbol": report.company.ticker_symbol if report.company else None,
            "report_type": report.report_type.value if report.report_type else None,
            "fiscal_period": report.fiscal_period,
            "filing_date": report.filing_date.isoformat() if report.filing_date else None,
            "processing_status": report.processing_status.value if report.processing_status else None,
        }
    return AnalysisResponse(
        id=str(analysis.id),
        report_id=str(analysis.report_id),
        optimism_score=analysis.optimism_score,
        optimism_confidence=analysis.optimism_confidence,
        risk_score=analysis.risk_score,
        risk_confidence=analysis.risk_confidence,
        uncertainty_score=analysis.uncertainty_score,
        uncertainty_confidence=analysis.uncertainty_confidence,
        key_themes=analysis.key_themes or [],
        risk_indicators=analysis.risk_indicators or [],
        narrative_sections=analysis.narrative_sections or {},
        financial_metrics=analysis.financial_metrics,
        processing_time_seconds=analysis.processing_time_seconds,
        model_version=analysis.model_version,
        created_at=analysis.created_at.isoformat() if getattr(analysis, 'created_at', None) else "",
        report=report_dict,
    )


@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(
    report_id: str = None,
    company_id: str = None,
    skip: int = 0,
    limit: int | None = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List narrative analyses with optional filtering (database-backed)."""
    q = db.query(NA)
    # Join to report when we need company filter or to embed report summary
    q = q.join(FinancialReport, FinancialReport.id == NA.report_id)

    if report_id:
        try:
            import uuid as _uuid
            q = q.filter(NA.report_id == _uuid.UUID(report_id))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report_id")

    if company_id:
        try:
            import uuid as _uuid
            q = q.filter(FinancialReport.company_id == _uuid.UUID(company_id))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid company_id")

    q = q.order_by(NA.created_at.desc())
    # Apply pagination only when a limit is explicitly provided; otherwise return all
    if limit is not None:
        q = q.offset(max(0, skip)).limit(max(1, min(int(limit), 500)))

    rows: List[tuple[NA, FinancialReport]] = q.add_entity(FinancialReport).all()
    return [_to_response(na, fr) for (na, fr) in rows]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed analysis results for a specific analysis (database-backed)."""
    try:
        import uuid as _uuid
        analysis_uuid = _uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analysis ID format")

    na: NA | None = db.query(NA).filter(NA.id == analysis_uuid).first()
    if not na:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    report: FinancialReport | None = db.query(FinancialReport).filter(FinancialReport.id == na.report_id).first()
    return _to_response(na, report)


@router.post("/compare", response_model=ComparisonResponse)
async def compare_reports(
    comparison_request: ComparisonRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare narrative tone between two financial reports using stored analyses."""
    try:
        delta: NarrativeDelta = DeltaAnalyzer.compare_reports(
            db,
            base_report_id=comparison_request.base_report_id,
            comparison_report_id=comparison_request.comparison_report_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    significant_changes = delta.get_alert_messages()
    summary = delta.get_sentiment_change_summary()

    return ComparisonResponse(
        id=str(delta.id),
        base_analysis_id=str(delta.base_analysis_id),
        comparison_analysis_id=str(delta.comparison_analysis_id),
        optimism_delta=delta.optimism_delta,
        risk_delta=delta.risk_delta,
        uncertainty_delta=delta.uncertainty_delta,
        overall_sentiment_delta=delta.overall_sentiment_delta,
        significant_changes=significant_changes,
        delta_summary=summary["overall_change"]["direction"],
    )


@router.post("/search/similar")
async def search_similar_content(
    search_request: SimilaritySearchRequest,
    current_user: Dict[str, Any] = Depends(require_enterprise_tier)
):
    """Find similar narrative content using vector similarity search.
    
    Requires Enterprise subscription.
    TODO: Implement vector similarity search using embeddings.
    """
    # TODO: Generate embedding for query text
    # TODO: Search narrative_embeddings table for similar vectors
    # TODO: Return matching content with similarity scores
    
    # Mock similarity search results
    mock_results = [
        {
            "report_id": "report-1",
            "text_chunk": "Management remains optimistic about future growth prospects despite current market challenges.",
            "similarity_score": 0.87,
            "company": "Apple Inc.",
            "report_type": "10-K",
            "filing_date": "2024-10-31"
        },
        {
            "report_id": "report-3",
            "text_chunk": "We are confident in our ability to navigate the evolving market landscape and capitalize on emerging opportunities.",
            "similarity_score": 0.82,
            "company": "Microsoft Corporation", 
            "report_type": "10-Q",
            "filing_date": "2024-07-31"
        }
    ]
    
    return {"results": mock_results[:search_request.limit]}


@router.get("/trends/{company_id}")
async def get_sentiment_trends(
    company_id: str,
    periods: int = 8,  # Number of reporting periods to include
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get sentiment trend analysis for a company over time.
    
    TODO: Replace with database aggregation query.
    """
    # TODO: Query analyses for company over specified periods
    # TODO: Calculate trend metrics and changes over time
    
    # Mock trend data
    mock_trends = {
        "company_id": company_id,
        "periods_analyzed": 6,
        "trend_data": [
            {"period": "Q1 2024", "overall_sentiment": 0.65, "optimism": 0.70, "risk": 0.35},
            {"period": "Q2 2024", "overall_sentiment": 0.72, "optimism": 0.75, "risk": 0.28},
            {"period": "Q3 2024", "overall_sentiment": 0.68, "optimism": 0.71, "risk": 0.32},
            {"period": "Q4 2024", "overall_sentiment": 0.74, "optimism": 0.78, "risk": 0.26},
        ],
        "trend_summary": {
            "overall_direction": "improving",
            "volatility": "moderate",
            "key_changes": [
                "Steady improvement in optimism scores",
                "Decreasing risk perception over time",
                "Stable uncertainty levels"
            ]
        }
    }
    
    return mock_trends
