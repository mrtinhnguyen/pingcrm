"""Tests for the FastAPI app setup and health endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    resp = await client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORS should allow localhost:3000
    assert resp.status_code in (200, 204)


@pytest.mark.asyncio
async def test_unknown_route(client: AsyncClient):
    resp = await client.get("/api/v1/nonexistent")
    assert resp.status_code == 404
