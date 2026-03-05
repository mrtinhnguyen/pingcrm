"""Tests for contacts API endpoints."""
import io
import uuid

import pytest
from httpx import AsyncClient

from app.models.contact import Contact
from app.models.user import User


@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/contacts", json={
        "full_name": "Jane Smith",
        "emails": ["jane@test.com"],
        "company": "TestCorp",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["full_name"] == "Jane Smith"
    assert data["emails"] == ["jane@test.com"]


@pytest.mark.asyncio
async def test_list_contacts(client: AsyncClient, auth_headers: dict, test_contact: Contact):
    resp = await client.get("/api/v1/contacts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_list_contacts_search(client: AsyncClient, auth_headers: dict, test_contact: Contact):
    resp = await client.get("/api/v1/contacts?search=John", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    resp = await client.get("/api/v1/contacts?search=NonExistent", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 0


@pytest.mark.asyncio
async def test_list_contacts_search_escapes_wildcards(client: AsyncClient, auth_headers: dict, test_contact: Contact):
    resp = await client.get("/api/v1/contacts?search=%25", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 0


@pytest.mark.asyncio
async def test_get_contact(client: AsyncClient, auth_headers: dict, test_contact: Contact):
    resp = await client.get(f"/api/v1/contacts/{test_contact.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_get_contact_not_found(client: AsyncClient, auth_headers: dict):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/contacts/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_contact(client: AsyncClient, auth_headers: dict, test_contact: Contact):
    resp = await client.put(f"/api/v1/contacts/{test_contact.id}", json={
        "company": "New Corp",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["company"] == "New Corp"


@pytest.mark.asyncio
async def test_delete_contact(client: AsyncClient, auth_headers: dict, test_contact: Contact):
    resp = await client.delete(f"/api/v1/contacts/{test_contact.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True

    resp = await client.get(f"/api/v1/contacts/{test_contact.id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_import_csv(client: AsyncClient, auth_headers: dict):
    csv_content = "full_name,emails,phones,company,twitter_handle,telegram_username,notes,tags\n"
    csv_content += "Alice Bob,alice@test.com,+1111,TestCo,@alice,alice_tg,Some notes,vip;friend\n"
    csv_content += "Bob Carol,bob@test.com,,OtherCo,,,,"

    resp = await client.post(
        "/api/v1/contacts/import/csv",
        files={"file": ("contacts.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["created"]) == 2
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_import_csv_bad_file(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/contacts/import/csv",
        files={"file": ("data.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_contacts_require_auth(client: AsyncClient):
    resp = await client.get("/api/v1/contacts")
    assert resp.status_code == 401
