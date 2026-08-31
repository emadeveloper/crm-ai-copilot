"""Task 5.1 / 5.5 — REST API (spec: lead-api). App + in-memory fakes, no DB."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.domain.contact_details import ContactDetails
from app.domain.lead import Lead
from app.domain.value_objects import Email
from app.main import create_app
from tests.fakes import InMemoryLeadRepository, sample_analysis
from tests.fakes.container import make_fake_container

PAYLOAD = {
    "source": "website-form",
    "contact": {"name": "Ada Lovelace", "email": "ada@example.com", "message": "pricing?"},
}


@pytest_asyncio.fixture
async def repo() -> InMemoryLeadRepository:
    return InMemoryLeadRepository()


@pytest_asyncio.fixture
async def client(repo: InMemoryLeadRepository) -> AsyncIterator[AsyncClient]:
    app = create_app(container=make_fake_container(leads=repo), run_worker=False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_post_leads_creates_and_returns_201(client: AsyncClient) -> None:
    resp = await client.post("/leads", json=PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["deduplicated"] is False
    assert body["id"]


async def test_post_leads_rejects_a_bad_email_with_422(client: AsyncClient) -> None:
    bad = {"source": "x", "contact": {"name": "Ada", "email": "not-an-email"}}
    resp = await client.post("/leads", json=bad)
    assert resp.status_code == 422


async def test_post_leads_rejects_a_missing_name_with_422(client: AsyncClient) -> None:
    bad = {"source": "x", "contact": {"email": "ada@example.com"}}
    resp = await client.post("/leads", json=bad)
    assert resp.status_code == 422


async def test_post_leads_deduplicates_with_200(client: AsyncClient) -> None:
    first = await client.post("/leads", json=PAYLOAD)
    second = await client.post("/leads", json=PAYLOAD)
    assert second.status_code == 200
    assert second.json()["deduplicated"] is True
    assert second.json()["id"] == first.json()["id"]


async def test_get_leads_lists_newest_first(
    client: AsyncClient, repo: InMemoryLeadRepository
) -> None:
    base = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
    for i, name in enumerate(["First", "Second", "Third"]):
        await repo.save(
            Lead.register(
                source="form",
                contact=ContactDetails(name=name, email=Email(f"{name}@x.com")),
                now=base + timedelta(minutes=i),
            )
        )

    resp = await client.get("/leads")
    assert resp.status_code == 200
    names = [row["contact"]["name"] for row in resp.json()]
    assert names == ["Third", "Second", "First"]


async def test_get_lead_returns_the_aggregate(
    client: AsyncClient, repo: InMemoryLeadRepository
) -> None:
    lead = Lead.register(
        source="form", contact=ContactDetails(name="Ada", email=Email("ada@example.com"))
    )
    await repo.save(lead)
    await repo.save_analysis(lead.id, sample_analysis())

    resp = await client.get(f"/leads/{lead.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(lead.id)
    assert body["score"]["value"] == 82
    assert body["score"]["band"] == "hot"
    assert body["reply_draft"]["subject"] == "Thanks for reaching out"


async def test_get_unknown_lead_returns_404(client: AsyncClient) -> None:
    resp = await client.get("/leads/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == 404
