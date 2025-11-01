import pytest


@pytest.mark.asyncio
async def test_security_and_trace_headers(client):
    r = await client.get("/health")
    # Security headers
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    # Trace headers
    assert r.headers.get("X-Request-ID")
    assert r.headers.get("X-Processing-Time")


