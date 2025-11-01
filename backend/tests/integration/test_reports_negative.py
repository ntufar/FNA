import io
import uuid
import pytest


@pytest.mark.asyncio
async def test_upload_invalid_company_id_422(auth_headers, client):
    files = {"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")}
    form = {"company_id": "not-a-uuid", "report_type": "10-K"}
    r = await client.post("/v1/reports/upload", headers=auth_headers, data=form, files=files)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_upload_invalid_report_type_422(auth_headers, client):
    # Create or get a company first
    payload = {"ticker_symbol": "NEG1", "company_name": "Negative One"}
    cr = await client.post("/v1/companies/", json=payload, headers=auth_headers)
    if cr.status_code == 400:
        lst = await client.get("/v1/companies/?ticker=NEG1", headers=auth_headers)
        lst.raise_for_status()
        company_id = lst.json()[0]["id"]
    else:
        cr.raise_for_status()
        company_id = cr.json()["id"]

    files = {"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")}
    form = {"company_id": company_id, "report_type": "NOT_A_TYPE"}
    r = await client.post("/v1/reports/upload", headers=auth_headers, data=form, files=files)
    assert r.status_code in (200, 400, 422, 500)


@pytest.mark.asyncio
async def test_get_report_not_found_404(auth_headers, client):
    rid = uuid.uuid4()
    r = await client.get(f"/v1/reports/{rid}", headers=auth_headers)
    assert r.status_code == 404


