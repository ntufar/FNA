import pytest


@pytest.mark.asyncio
async def test_head_health(client):
    r = await client.request("HEAD", "/health")
    # Some builds don't add HEAD automatically; accept 405 as well
    assert r.status_code in (200, 405)


@pytest.mark.asyncio
async def test_auth_logout(auth_headers, client):
    r = await client.post("/v1/auth/logout", headers=auth_headers)
    assert r.status_code in (200, 204)


@pytest.mark.asyncio
async def test_company_detail_not_found(auth_headers, client):
    import uuid
    cid = uuid.uuid4()
    r = await client.get(f"/v1/companies/{cid}", headers=auth_headers)
    assert r.status_code == 404
