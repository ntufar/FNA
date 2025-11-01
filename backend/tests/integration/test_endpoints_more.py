import io
import uuid
from datetime import datetime, timezone

import pytest

from src.models.financial_report import FinancialReport, ProcessingStatus, ReportType, FileFormat, DownloadSource
from sqlalchemy.orm import Session


@pytest.mark.asyncio
async def test_companies_get_invalid_and_notfound(auth_headers, client):
    r = await client.get("/v1/companies/not-a-uuid", headers=auth_headers)
    assert r.status_code == 400
    r2 = await client.get(f"/v1/companies/{uuid.uuid4()}", headers=auth_headers)
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_reports_get_invalid_report(auth_headers, client):
    r = await client.get("/v1/reports/something", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_report_analysis_status_codes(auth_headers, client, db_session: Session):
    # Ensure a company exists and get its ID
    comp_payload = {"ticker_symbol": "STATU", "company_name": "Status Co"}
    cr = await client.post("/v1/companies/", json=comp_payload, headers=auth_headers)
    if cr.status_code == 400:
        # fetch existing id
        lst = await client.get("/v1/companies/?ticker=STATU", headers=auth_headers)
        lst.raise_for_status()
        company_id = lst.json()[0]["id"]
    else:
        cr.raise_for_status()
        company_id = cr.json()["id"]
    # Create report with PENDING => expect 202
    pending_report = FinancialReport(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        report_type=ReportType.OTHER,
        fiscal_period="FY 2024",
        filing_date=datetime.now(timezone.utc).date(),
        file_path="/tmp/pending.txt",
        file_format=FileFormat.TXT,
        file_size_bytes=1,
        download_source=DownloadSource.MANUAL_UPLOAD,
        processing_status=ProcessingStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(pending_report)
    db_session.commit()
    r = await client.get(f"/v1/reports/{pending_report.id}/analysis", headers=auth_headers)
    assert r.status_code == 202

    # Create report with FAILED => expect 422
    failed_report = FinancialReport(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        report_type=ReportType.OTHER,
        fiscal_period="FY 2024",
        filing_date=datetime.now(timezone.utc).date(),
        file_path="/tmp/failed.txt",
        file_format=FileFormat.TXT,
        file_size_bytes=1,
        download_source=DownloadSource.MANUAL_UPLOAD,
        processing_status=ProcessingStatus.FAILED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(failed_report)
    db_session.commit()
    r2 = await client.get(f"/v1/reports/{failed_report.id}/analysis", headers=auth_headers)
    assert r2.status_code == 422


@pytest.mark.asyncio
async def test_pro_tier_required_for_sec_download(client):
    # Register/login a Basic user
    email = f"basic_{uuid.uuid4().hex[:8]}@example.com"
    reg = await client.post("/v1/auth/register", json={
        "email": email,
        "password": "StrongP@ssw0rd!",
        "full_name": "Basic User",
        "subscription_tier": "Basic"
    })
    # If 400 (exists), just login
    if reg.status_code not in (200, 201, 400):
        reg.raise_for_status()
    login = await client.post("/v1/auth/login", json={"email": email, "password": "StrongP@ssw0rd!"})
    login.raise_for_status()
    token = login.json()["access_token"]
    basic_headers = {"Authorization": f"Bearer {token}"}

    # Attempt SEC download -> should be forbidden before any external call
    payload = {"ticker_symbol": "AAPL", "report_type": "10-K"}
    resp = await client.post("/v1/reports/download", json=payload, headers=basic_headers)
    assert resp.status_code == 403


