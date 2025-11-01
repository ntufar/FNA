import io
import uuid
import pytest


@pytest.mark.asyncio
async def test_companies_reports_listing_flow(auth_headers, client):
    # Create or fetch a company
    payload = {"ticker_symbol": "RPTZ", "company_name": "Reports Zero"}
    cr = await client.post("/v1/companies/", json=payload, headers=auth_headers)
    if cr.status_code == 400:
        lst = await client.get("/v1/companies/?ticker=RPTZ", headers=auth_headers)
        lst.raise_for_status()
        company_id = lst.json()[0]["id"]
    else:
        cr.raise_for_status()
        company_id = cr.json()["id"]

    # List reports for company (likely empty, but covers code path)
    r = await client.get(f"/v1/companies/{company_id}/reports?limit=5", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "reports" in data and "company" in data


@pytest.mark.asyncio
async def test_reports_upload_invalid_mime(auth_headers, client):
    # Need a company id
    payload = {"ticker_symbol": "UPBD", "company_name": "Upload Bad"}
    cr = await client.post("/v1/companies/", json=payload, headers=auth_headers)
    if cr.status_code == 400:
        lst = await client.get("/v1/companies/?ticker=UPBD", headers=auth_headers)
        lst.raise_for_status()
        company_id = lst.json()[0]["id"]
    else:
        cr.raise_for_status()
        company_id = cr.json()["id"]

    files = {"file": ("bad.zip", io.BytesIO(b"bad"), "application/zip")}
    form = {"company_id": company_id, "report_type": "Other"}
    r = await client.post("/v1/reports/upload", headers=auth_headers, data=form, files=files)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reports_batch_limit_exceeded_pro(auth_headers, client):
    # Auth is Pro per fixture → limit is 7
    batch = [{"stub": i} for i in range(8)]
    r = await client.post("/v1/reports/batch", json=batch, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_auth_refresh_not_implemented(client):
    r = await client.post("/v1/auth/refresh?refresh_token=abc")
    assert r.status_code == 501


@pytest.mark.asyncio
async def test_unauthorized_access_rejected(client):
    # Missing/invalid token should yield 401
    r = await client.get("/v1/companies/")
    assert r.status_code == 403


