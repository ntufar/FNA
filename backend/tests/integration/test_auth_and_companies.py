import pytest


@pytest.mark.asyncio
async def test_auth_me(auth_headers, client):
    r = await client.get("/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "email" in data and "subscription_tier" in data


@pytest.mark.asyncio
async def test_companies_pagination_and_filters(auth_headers, client):
    # Create few companies (ignore 400 if exists)
    for tick, name in [("PG01", "Page One"), ("PG02", "Page Two")]:
        resp = await client.post("/v1/companies/", json={"ticker_symbol": tick, "company_name": name}, headers=auth_headers)
        if resp.status_code not in (200, 400):
            resp.raise_for_status()

    # Pagination
    r = await client.get("/v1/companies/?skip=0&limit=1", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Filter by ticker substring
    r2 = await client.get("/v1/companies/?ticker=PG", headers=auth_headers)
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


