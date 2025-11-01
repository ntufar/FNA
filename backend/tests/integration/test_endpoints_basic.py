import pytest


@pytest.mark.asyncio
async def test_health_endpoints(client):
    r = await client.get("/health")
    assert r.status_code in (200, 503)
    r2 = await client.get("/health/live")
    assert r2.status_code == 200
    r3 = await client.get("/health/ready")
    assert r3.status_code in (200, 503)


@pytest.mark.asyncio
async def test_companies_add_and_list(auth_headers, client):
    payload = {"ticker_symbol": "COVR", "company_name": "Coverage Inc"}
    r = await client.post("/v1/companies/", json=payload, headers=auth_headers)
    # Allow 400 if already created by prior run
    assert r.status_code in (200, 400)
    r2 = await client.get("/v1/companies/?ticker=COVR", headers=auth_headers)
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


@pytest.mark.asyncio
async def test_reports_analysis_error_statuses(auth_headers, client):
    # Invalid UUID
    r = await client.get("/v1/reports/not-a-uuid/analysis", headers=auth_headers)
    assert r.status_code == 400

