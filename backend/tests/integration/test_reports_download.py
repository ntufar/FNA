import uuid
import os
import pytest

from sqlalchemy.orm import Session


@pytest.mark.asyncio
async def test_reports_download_real_sec_success(client, auth_headers, db_session: Session):
    # Ensure a non-empty SEC user agent for compliance
    os.environ.setdefault("SEC_USER_AGENT", "FNA Test Suite test@example.com")

    candidate_tickers = [
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "EL"
    ]
    report_types = ["10-K", "10-Q", "8-K"]

    from src.models.financial_report import FinancialReport

    success_response = None
    used_payload = None

    for tkr in candidate_tickers:
        for rtype in report_types:
            payload = {"ticker_symbol": tkr, "report_type": rtype}
            r = await client.post("/v1/reports/download", json=payload, headers=auth_headers)
            # 200 = success; 404 = no recent filings; 429/5xx may be transient
            if r.status_code == 200:
                success_response = r
                used_payload = payload
                break
            elif r.status_code == 404:
                continue
            else:
                # Try next combination on transient errors
                continue
        if success_response is not None:
            break

    assert success_response is not None, "Could not download any report from SEC across candidates"

    data = success_response.json()
    assert "report_id" in data
    assert data["processing_status"] == "PENDING"
    rid = uuid.UUID(data["report_id"])  # valid UUID

    # Verify DB record exists
    fr = db_session.query(FinancialReport).filter(FinancialReport.id == rid).first()
    assert fr is not None, f"FinancialReport must exist after download (ticker={used_payload['ticker_symbol']}, type={used_payload['report_type']})"
    assert fr.fiscal_period is not None and fr.fiscal_period != ""
    assert fr.file_path and isinstance(fr.file_path, str)


