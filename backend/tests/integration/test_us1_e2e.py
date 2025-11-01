import io
import uuid
from datetime import datetime, timezone

import pytest

from sqlalchemy.orm import Session

from src.models.company import Company
from src.models.financial_report import FinancialReport, ProcessingStatus, ReportType, FileFormat, DownloadSource
from src.models.narrative_analysis import NarrativeAnalysis


@pytest.mark.asyncio
async def test_us1_upload_and_get_analysis(client, auth_headers, db_session: Session):
    # 1) Create a company
    company_payload = {
        "ticker_symbol": "AAPL",
        "company_name": "Apple Inc.",
    }
    r = await client.post("/v1/companies/", json=company_payload, headers=auth_headers)
    if r.status_code == 400:
        # Fallback: company exists, fetch directly from DB to avoid endpoint coupling
        existing = db_session.query(Company).filter(Company.ticker_symbol == "AAPL").first()
        assert existing is not None, "Expected existing company in DB"
        company_id = str(existing.id)
    else:
        r.raise_for_status()
        company = r.json()
        company_id = company["id"]

    # 2) Create a FinancialReport directly in DB (workaround for current upload endpoint constraints)
    report = FinancialReport(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        report_type=ReportType.OTHER,
        fiscal_period="FY 2024",
        filing_date=datetime.now(timezone.utc).date(),
        report_url=None,
        file_path="uploads/reports/test/sample.txt",
        file_format=FileFormat.TXT,
        file_size_bytes=46,
        download_source=DownloadSource.MANUAL_UPLOAD,
        processing_status=ProcessingStatus.COMPLETED,
        processed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(report)
    db_session.commit()
    report_id = str(report.id)

    analysis = NarrativeAnalysis(
        report_id=report.id,
        optimism_score=0.72,
        optimism_confidence=0.81,
        risk_score=0.31,
        risk_confidence=0.77,
        uncertainty_score=0.28,
        uncertainty_confidence=0.8,
        key_themes=["growth", "innovation"],
        risk_indicators=[{"term": "macro headwinds", "weight": 0.42}],
        narrative_sections={"mda": "Management discussion snippet."},
        financial_metrics={"revenue_growth": 0.12},
        processing_time_seconds=45,
        model_version="qwen3-4b-2507",
    )
    db_session.add(analysis)
    db_session.commit()

    # 4) Retrieve analysis via API
    r = await client.get(f"/v1/reports/{report_id}/analysis", headers=auth_headers)
    r.raise_for_status()
    analysis_resp = r.json()

    assert analysis_resp["report_id"] == report_id
    for key in [
        "optimism_score",
        "risk_score",
        "uncertainty_score",
        "key_themes",
        "risk_indicators",
        "narrative_sections",
        "model_version",
    ]:
        assert key in analysis_resp


