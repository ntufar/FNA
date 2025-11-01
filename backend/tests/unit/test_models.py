from datetime import datetime, timedelta, timezone
import uuid

from src.models.company import Company
from src.models.financial_report import FinancialReport, ProcessingStatus, ReportType, FileFormat, DownloadSource
from src.models.narrative_analysis import NarrativeAnalysis


def test_company_reports_helpers():
    c = Company(
        id=uuid.uuid4(),
        ticker_symbol="TEST",
        company_name="Test Corp",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # No reports initially
    assert c.latest_report is None
    assert c.reports_count == 0

    # Add two reports, different dates
    r1 = FinancialReport(
        id=uuid.uuid4(),
        company_id=c.id,
        report_type=ReportType.TEN_K,
        fiscal_period="FY 2024",
        filing_date=datetime(2024, 10, 31, tzinfo=timezone.utc).date(),
        report_url=None,
        file_path="/tmp/a.html",
        file_format=FileFormat.HTML,
        file_size_bytes=100,
        download_source=DownloadSource.MANUAL_UPLOAD,
        processing_status=ProcessingStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    r2 = FinancialReport(
        id=uuid.uuid4(),
        company_id=c.id,
        report_type=ReportType.TEN_Q,
        fiscal_period="Q3 2024",
        filing_date=datetime(2024, 7, 31, tzinfo=timezone.utc).date(),
        report_url=None,
        file_path="/tmp/b.html",
        file_format=FileFormat.HTML,
        file_size_bytes=200,
        download_source=DownloadSource.MANUAL_UPLOAD,
        processing_status=ProcessingStatus.PROCESSING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    c.financial_reports = [r1, r2]
    assert c.reports_count == 2
    assert c.latest_report == r1


def test_financial_report_helpers():
    fr = FinancialReport(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        report_type=ReportType.OTHER,
        fiscal_period="FY 2024",
        filing_date=datetime.now(timezone.utc).date(),
        report_url=None,
        file_path="/tmp/file.txt",
        file_format=FileFormat.TXT,
        file_size_bytes=1024 * 1024 * 5,  # 5MB
        download_source=DownloadSource.SEC_AUTO,
        processing_status=ProcessingStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert fr.is_pending
    fr.set_processing()
    assert fr.is_processing
    fr.set_completed()
    assert fr.is_completed
    assert fr.processing_time_minutes is not None
    fr.reset_to_pending()
    assert fr.is_pending
    assert fr.validate_file_size(50)
    assert fr.validate_fiscal_period()


def test_narrative_analysis_helpers():
    na = NarrativeAnalysis(
        id=uuid.uuid4(),
        report_id=uuid.uuid4(),
        optimism_score=0.8,
        optimism_confidence=0.9,
        risk_score=0.2,
        risk_confidence=0.7,
        uncertainty_score=0.3,
        uncertainty_confidence=0.8,
        key_themes=["growth", "efficiency"],
        risk_indicators=[{"term": "macro", "weight": 0.4}],
        narrative_sections={"mda": "text"},
        financial_metrics={"rev": 1},
        processing_time_seconds=45,
        model_version="qwen3-4b-2507",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert na.validate_scores()
    assert na.validate_themes()
    assert na.overall_sentiment_score >= 0
    assert na.average_confidence > 0
    assert na.is_high_confidence
    assert na.is_optimistic
    assert not na.is_risky
    assert na.processing_time_minutes == 0.75
    assert na.meets_performance_requirement
    summary = na.get_sentiment_summary()
    assert "overall_sentiment_score" in summary
    grouped = na.get_themes_by_category(["growth"])
    assert grouped["growth"]

    prev = NarrativeAnalysis(
        id=uuid.uuid4(),
        report_id=na.report_id,
        optimism_score=0.7,
        optimism_confidence=0.8,
        risk_score=0.25,
        risk_confidence=0.7,
        uncertainty_score=0.35,
        uncertainty_confidence=0.7,
        key_themes=["growth"],
        risk_indicators=[],
        narrative_sections={},
        financial_metrics=None,
        processing_time_seconds=50,
        model_version="qwen3-4b-2507",
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
        updated_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    delta = na.compare_with_previous(prev)
    assert "optimism_delta" in delta


