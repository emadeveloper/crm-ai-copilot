"""Task 3.1 — SubmitLead use case (spec: lead-api / Lead submission over REST)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.submit_lead import SubmitLead, SubmitLeadCommand
from app.domain.contact_details import ContactDetails
from app.domain.ports import TaskKind
from app.domain.status import LeadStatus
from app.domain.value_objects import Email
from tests.fakes import InMemoryLeadRepository, InMemoryTaskQueue, fixed_clock

NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def _command(**contact: object) -> SubmitLeadCommand:
    fields: dict[str, object] = {"name": "Ada Lovelace", "email": Email("ada@example.com")}
    fields.update(contact)
    return SubmitLeadCommand(source="website-form", contact=ContactDetails(**fields))  # type: ignore[arg-type]


@pytest.fixture
def repo() -> InMemoryLeadRepository:
    return InMemoryLeadRepository()


@pytest.fixture
def queue() -> InMemoryTaskQueue:
    return InMemoryTaskQueue()


@pytest.fixture
def submit(repo: InMemoryLeadRepository, queue: InMemoryTaskQueue) -> SubmitLead:
    return SubmitLead(
        leads=repo, queue=queue, dedup_window=timedelta(hours=24), clock=fixed_clock(NOW)
    )


async def test_new_lead_is_persisted_received_and_queued_for_enrichment(
    submit: SubmitLead, repo: InMemoryLeadRepository, queue: InMemoryTaskQueue
) -> None:
    result = await submit.execute(_command())

    assert result.deduplicated is False
    stored = await repo.get_aggregate(result.lead_id)
    assert stored is not None
    assert stored.lead.status is LeadStatus.RECEIVED
    assert stored.lead.created_at == NOW
    assert queue.enqueued == [(TaskKind.ENRICH, result.lead_id)]


async def test_duplicate_within_the_window_returns_the_original_and_does_not_re_queue(
    submit: SubmitLead, queue: InMemoryTaskQueue
) -> None:
    first = await submit.execute(_command())
    second = await submit.execute(_command(message="second try"))

    assert second.deduplicated is True
    assert second.lead_id == first.lead_id
    assert queue.enqueued == [(TaskKind.ENRICH, first.lead_id)]  # only the first


async def test_same_email_different_source_is_not_a_duplicate(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue
) -> None:
    submit = SubmitLead(leads=repo, queue=queue, clock=fixed_clock(NOW))
    a = await submit.execute(SubmitLeadCommand(source="website-form", contact=_command().contact))
    b = await submit.execute(SubmitLeadCommand(source="linkedin-ad", contact=_command().contact))

    assert a.lead_id != b.lead_id
    assert b.deduplicated is False
    assert len(queue.enqueued) == 2


async def test_a_stale_prior_lead_does_not_deduplicate(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue
) -> None:
    old = SubmitLead(leads=repo, queue=queue, clock=fixed_clock(NOW - timedelta(days=2)))
    await old.execute(_command())

    fresh = SubmitLead(
        leads=repo, queue=queue, dedup_window=timedelta(hours=24), clock=fixed_clock(NOW)
    )
    result = await fresh.execute(_command())

    assert result.deduplicated is False
    assert len(queue.enqueued) == 2
