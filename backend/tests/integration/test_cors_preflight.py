import pytest


@pytest.mark.asyncio
async def test_cors_preflight_health(client):
    # Exercise CORS middleware path with OPTIONS request
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    r = await client.options("/health", headers=headers)
    # FastAPI CORS may return 200 or 204 depending on configuration
    assert r.status_code in (200, 204)
    # CORS headers should be present
    assert r.headers.get("access-control-allow-origin") in ("*", "http://localhost:3000")
    assert r.headers.get("access-control-allow-methods")


