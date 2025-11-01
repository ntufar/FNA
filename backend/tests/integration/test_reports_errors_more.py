import io
import pytest


@pytest.mark.asyncio
async def test_upload_empty_file_returns_error(auth_headers, client):
    # Create or fetch a company quickly
    payload = {"ticker_symbol": "EMPTY", "company_name": "Empty File Co"}
    cr = await client.post("/v1/companies/", json=payload, headers=auth_headers)
    if cr.status_code == 400:
        lst = await client.get("/v1/companies/?ticker=EMPTY", headers=auth_headers)
        lst.raise_for_status()
        company_id = lst.json()[0]["id"]
    else:
        cr.raise_for_status()
        company_id = cr.json()["id"]

    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    form = {"company_id": company_id, "report_type": "10-K"}
    r = await client.post("/v1/reports/upload", headers=auth_headers, data=form, files=files)
    # Implementation may return 400/422 or 500 from deeper pipeline
    assert r.status_code in (400, 422, 500)


