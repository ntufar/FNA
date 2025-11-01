import uuid
from datetime import date

import pytest

from src.models.company import Company
from src.models.financial_report import FinancialReport
from src.models.narrative_analysis import NarrativeAnalysis


@pytest.mark.asyncio
async def test_company_trends_returns_timeline(auth_headers, client, db_session):
    # Create a company via API to respect auth and business rules
    payload = {"ticker_symbol": "TRND", "company_name": "Trend Co"}
    r = await client.post("/v1/companies/", json=payload, headers=auth_headers)
    assert r.status_code in (200, 201, 400)

    # Resolve company id (get from list to be robust)
    r_list = await client.get("/v1/companies/?ticker=TRND", headers=auth_headers)
    assert r_list.status_code == 200
    companies = r_list.json()
    assert isinstance(companies, list) and len(companies) >= 1
    company_id = companies[0]["id"]

    # Seed two reports + analyses directly in DB
    company_uuid = uuid.UUID(company_id)

    rep1 = FinancialReport(
        id=uuid.uuid4(),
        company_id=company_uuid,
        report_type="10-K",
        fiscal_period="FY 2023",
        filing_date=date(2024, 2, 1),
        file_path="/tmp/r1",
        file_format="PDF",
        file_size_bytes=100,
        download_source="MANUAL_UPLOAD",
        processing_status="COMPLETED",
    )

    rep2 = FinancialReport(
        id=uuid.uuid4(),
        company_id=company_uuid,
        report_type="10-K",
        fiscal_period="FY 2024",
        filing_date=date(2025, 2, 1),
        file_path="/tmp/r2",
        file_format="PDF",
        file_size_bytes=120,
        download_source="MANUAL_UPLOAD",
        processing_status="COMPLETED",
    )

    db_session.add_all([rep1, rep2])
    db_session.flush()

    an1 = NarrativeAnalysis(
        id=uuid.uuid4(),
        report_id=rep1.id,
        optimism_score=0.6,
        risk_score=0.2,
        uncertainty_score=0.3,
        key_themes=[],
        risk_indicators=[],
        narrative_sections={},
        processing_time_seconds=10,
        model_version="test",
    )

    an2 = NarrativeAnalysis(
        id=uuid.uuid4(),
        report_id=rep2.id,
        optimism_score=0.7,
        risk_score=0.25,
        uncertainty_score=0.28,
        key_themes=[],
        risk_indicators=[],
        narrative_sections={},
        processing_time_seconds=11,
        model_version="test",
    )

    db_session.add_all([an1, an2])
    db_session.commit()

    # Call trends endpoint
    r_trends = await client.get(f"/v1/companies/{company_id}/trends", headers=auth_headers)
    assert r_trends.status_code == 200
    data = r_trends.json()

    assert "company" in data
    assert "timeline" in data and isinstance(data["timeline"], list)
    assert len(data["timeline"]) >= 2
    assert {"date", "optimism", "risk", "uncertainty"}.issubset(data["timeline"][0].keys())
    assert "period_over_period" in data
    assert "rolling_average" in data


