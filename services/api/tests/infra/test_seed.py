"""Task 5.6 — synthetic lead seeding."""

from __future__ import annotations

from app.application.submit_lead import SubmitLead
from app.seed import SYNTHETIC_LEADS, seed_leads
from tests.fakes import InMemoryLeadRepository, InMemoryTaskQueue


async def test_seed_submits_every_synthetic_lead() -> None:
    repo = InMemoryLeadRepository()
    queue = InMemoryTaskQueue()
    submit = SubmitLead(leads=repo, queue=queue)

    count = await seed_leads(submit)

    assert count == len(SYNTHETIC_LEADS)
    listed = await repo.list_aggregates(limit=100, offset=0)
    assert len(listed) == len(SYNTHETIC_LEADS)
    assert len(queue.enqueued) == len(SYNTHETIC_LEADS)


async def test_seed_accepts_a_custom_list() -> None:
    submit = SubmitLead(leads=InMemoryLeadRepository(), queue=InMemoryTaskQueue())
    custom = [{"source": "test", "contact": {"name": "Only One", "email": "one@example.com"}}]
    assert await seed_leads(submit, custom) == 1


def test_synthetic_data_is_not_real_pii() -> None:
    # Free-tier Gemini may train on prompts — the deployed demo must use fake data only.
    assert len(SYNTHETIC_LEADS) >= 5
    for raw in SYNTHETIC_LEADS:
        assert raw["contact"]["email"].endswith(("example.com", "example.org", "test"))
