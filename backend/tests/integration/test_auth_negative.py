import pytest


@pytest.mark.asyncio
async def test_auth_me_with_invalid_token(client):
    headers = {"Authorization": "Bearer invalid.token.value"}
    r = await client.get("/v1/auth/me", headers=headers)
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_companies_with_malformed_authorization_header(client):
    headers = {"Authorization": "TotallyWrong abc"}
    r = await client.get("/v1/companies/", headers=headers)
    assert r.status_code in (401, 403)
