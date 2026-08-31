"""Task 5.2 — GraphQL query slice (spec: lead-api / retrieval over GraphQL)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.domain.contact_details import ContactDetails
from app.domain.lead import Lead
from app.domain.value_objects import Email
from app.main import create_app
from tests.fakes import InMemoryLeadRepository, sample_analysis
from tests.fakes.container import make_fake_container

BASE = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


@pytest_asyncio.fixture
async def repo() -> InMemoryLeadRepository:
    return InMemoryLeadRepository()


@pytest_asyncio.fixture
async def client(repo: InMemoryLeadRepository) -> AsyncIterator[AsyncClient]:
    app = create_app(container=make_fake_container(leads=repo), run_worker=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _gql(client: AsyncClient, query: str) -> dict[str, Any]:
    resp = await client.post("/graphql", json={"query": query})
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert "errors" not in payload, payload["errors"]
    data: dict[str, Any] = payload["data"]
    return data


async def test_lead_query_returns_the_same_aggregate_as_rest(
    client: AsyncClient, repo: InMemoryLeadRepository
) -> None:
    lead = Lead.register(
        source="website-form",
        contact=ContactDetails(name="Ada Lovelace", email=Email("ada@example.com")),
        now=BASE,
    )
    await repo.save(lead)
    await repo.save_analysis(lead.id, sample_analysis())

    data = await _gql(
        client,
        f'{{ lead(id: "{lead.id}") {{ status score {{ value band }} '
        f"enrichment {{ industry }} replyDraft {{ subject }} }} }}",
    )
    assert data["lead"]["status"] == "qualified" or data["lead"]["status"] == "received"
    assert data["lead"]["score"]["value"] == 82
    assert data["lead"]["score"]["band"] == "hot"
    assert data["lead"]["enrichment"]["industry"] == "fintech"
    assert data["lead"]["replyDraft"]["subject"] == "Thanks for reaching out"

    rest = (await client.get(f"/leads/{lead.id}")).json()
    assert rest["score"]["value"] == data["lead"]["score"]["value"]


async def test_lead_query_returns_null_for_unknown_id(client: AsyncClient) -> None:
    data = await _gql(client, '{ lead(id: "11111111-1111-1111-1111-111111111111") { id } }')
    assert data["lead"] is None


async def test_leads_query_paginates_newest_first(
    client: AsyncClient, repo: InMemoryLeadRepository
) -> None:
    for i, name in enumerate(["L0", "L1", "L2", "L3", "L4"]):
        await repo.save(
            Lead.register(
                source="form",
                contact=ContactDetails(name=name, email=Email(f"{name}@x.com")),
                now=BASE + timedelta(minutes=i),
            )
        )

    data = await _gql(client, "{ leads(limit: 2, offset: 1) { contact { name } } }")
    assert [row["contact"]["name"] for row in data["leads"]] == ["L3", "L2"]
