"""The browser dashboard is served from a different origin than the API."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from tests.fakes.container import make_fake_container

ORIGIN = "http://localhost:5173"


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app(container=make_fake_container(), run_worker=False, cors_origins=[ORIGIN])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_simple_request_gets_the_allow_origin_header(client: AsyncClient) -> None:
    resp = await client.get("/leads", headers={"Origin": ORIGIN})
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ORIGIN


async def test_preflight_is_allowed(client: AsyncClient) -> None:
    resp = await client.options(
        "/leads",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers["access-control-allow-origin"] == ORIGIN
    assert "POST" in resp.headers["access-control-allow-methods"]


async def test_unknown_origin_is_not_echoed(client: AsyncClient) -> None:
    resp = await client.get("/leads", headers={"Origin": "http://evil.example"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") != "http://evil.example"
