"""End-to-end: POST /leads -> worker enrich -> worker sync -> GET shows synced.

Covers the proposal's Success Criteria with in-memory adapters (no network, no DB).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.infra.worker import PipelineWorker
from app.main import create_app
from tests.fakes import FakeCrmGateway, FakeLLMProvider, InMemoryLeadRepository, InMemoryTaskQueue
from tests.fakes.container import make_fake_container

PAYLOAD = {
    "source": "website-form",
    "contact": {"name": "Ada Lovelace", "email": "ada@example.com", "message": "pricing for 200?"},
}


class _Harness:
    def __init__(self) -> None:
        self.repo = InMemoryLeadRepository()
        self.queue = InMemoryTaskQueue()
        self.llm = FakeLLMProvider()
        self.crm = FakeCrmGateway()
        self.container = make_fake_container(
            leads=self.repo, queue=self.queue, llm=self.llm, crm=self.crm
        )
        self.worker = PipelineWorker(
            queue=self.queue,
            enrich=self.container.enrich_lead(),
            sync=self.container.sync_lead_to_crm(),
            max_attempts=3,
            poll_interval=0.01,
        )


@pytest_asyncio.fixture
async def harness() -> _Harness:
    return _Harness()


@pytest_asyncio.fixture
async def client(harness: _Harness) -> AsyncIterator[AsyncClient]:
    app = create_app(container=harness.container, run_worker=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_synthetic_lead_flows_all_the_way_to_synced(
    client: AsyncClient, harness: _Harness
) -> None:
    created = await client.post("/leads", json=PAYLOAD)
    assert created.status_code == 201
    lead_id = created.json()["id"]

    assert await harness.worker.run_once() is True  # enrich
    assert await harness.worker.run_once() is True  # sync
    assert await harness.worker.run_once() is False  # queue drained

    detail = (await client.get(f"/leads/{lead_id}")).json()
    assert detail["status"] == "synced"
    assert detail["score"]["value"] == 82
    assert detail["reply_draft"]["subject"] == "Thanks for reaching out"
    assert detail["sync_state"]["status"] == "synced"
    assert detail["sync_state"]["crm_contact_id"]

    gql = await client.post(
        "/graphql",
        json={"query": f'{{ lead(id: "{lead_id}") {{ status syncState {{ status }} }} }}'},
    )
    assert gql.json()["data"]["lead"]["syncState"]["status"] == "synced"

    assert any("82" in note for _, note in harness.crm.notes)
    assert harness.llm.calls == 1
