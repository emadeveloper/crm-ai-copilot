"""Task 3.2 — EnrichLead use case (spec: ai-enrichment)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.enrich_lead import EnrichLead
from app.application.errors import LLMResponseInvalid, LLMTemporaryError
from app.domain.contact_details import ContactDetails
from app.domain.errors import LeadNotFound
from app.domain.lead import Lead
from app.domain.ports import TaskKind
from app.domain.status import LeadStatus
from app.domain.value_objects import Email, LeadId
from tests.fakes import (
    FakeLLMProvider,
    InMemoryLeadRepository,
    InMemoryTaskQueue,
    RecordingSleep,
    fixed_clock,
    sample_analysis,
)

NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


async def _received_lead(repo: InMemoryLeadRepository) -> Lead:
    lead = Lead.register(
        source="website-form",
        contact=ContactDetails(name="Ada", email=Email("ada@example.com"), message="pricing?"),
        now=NOW,
    )
    await repo.save(lead)
    return lead


def _enrich(
    repo: InMemoryLeadRepository,
    queue: InMemoryTaskQueue,
    llm: FakeLLMProvider,
    sleep: RecordingSleep,
    *,
    max_attempts: int = 3,
) -> EnrichLead:
    return EnrichLead(
        leads=repo,
        queue=queue,
        llm=llm,
        max_attempts=max_attempts,
        backoff_base=timedelta(seconds=2),
        sleep=sleep,
        clock=fixed_clock(NOW),
    )


@pytest.fixture
def repo() -> InMemoryLeadRepository:
    return InMemoryLeadRepository()


@pytest.fixture
def queue() -> InMemoryTaskQueue:
    return InMemoryTaskQueue()


@pytest.fixture
def sleep() -> RecordingSleep:
    return RecordingSleep()


async def test_happy_path_persists_analysis_qualifies_and_queues_sync(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue, sleep: RecordingSleep
) -> None:
    lead = await _received_lead(repo)
    llm = FakeLLMProvider(analysis=sample_analysis())

    await _enrich(repo, queue, llm, sleep).execute(lead.id)

    assert llm.calls == 1
    assert sleep.calls == []
    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None
    assert aggregate.lead.status is LeadStatus.QUALIFIED
    assert aggregate.score is not None and aggregate.score.value == 82
    assert aggregate.reply_draft is not None
    assert queue.enqueued == [(TaskKind.SYNC, lead.id)]


async def test_retries_with_backoff_then_succeeds(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue, sleep: RecordingSleep
) -> None:
    lead = await _received_lead(repo)
    llm = FakeLLMProvider(fail_times=2, error=LLMTemporaryError("429"))

    await _enrich(repo, queue, llm, sleep).execute(lead.id)

    assert llm.calls == 3
    assert sleep.calls == [2.0, 4.0]  # exponential backoff, no sleep after the last failure
    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None and aggregate.lead.status is LeadStatus.QUALIFIED


async def test_exhausted_retries_mark_the_lead_failed_without_partial_persist(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue, sleep: RecordingSleep
) -> None:
    lead = await _received_lead(repo)
    llm = FakeLLMProvider(fail_times=99, error=LLMTemporaryError("still down"))

    await _enrich(repo, queue, llm, sleep, max_attempts=3).execute(lead.id)

    assert llm.calls == 3
    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None
    assert aggregate.lead.status is LeadStatus.FAILED
    assert aggregate.lead.failure_reason is not None
    assert aggregate.score is None and aggregate.enrichment is None
    assert queue.enqueued == []


async def test_invalid_response_is_not_retried(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue, sleep: RecordingSleep
) -> None:
    lead = await _received_lead(repo)
    llm = FakeLLMProvider(fail_times=99, error=LLMResponseInvalid("score 140 out of range"))

    await _enrich(repo, queue, llm, sleep).execute(lead.id)

    assert llm.calls == 1
    assert sleep.calls == []
    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None and aggregate.lead.status is LeadStatus.FAILED


async def test_lead_already_past_enrichment_is_a_no_op(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue, sleep: RecordingSleep
) -> None:
    lead = await _received_lead(repo)
    lead.advance_to(LeadStatus.ENRICHING, now=NOW)
    lead.advance_to(LeadStatus.QUALIFIED, now=NOW)
    lead.advance_to(LeadStatus.SYNCING, now=NOW)
    lead.advance_to(LeadStatus.SYNCED, now=NOW)
    await repo.save(lead)
    llm = FakeLLMProvider()

    await _enrich(repo, queue, llm, sleep).execute(lead.id)

    assert llm.calls == 0
    assert queue.enqueued == []


async def test_unknown_lead_raises(
    repo: InMemoryLeadRepository, queue: InMemoryTaskQueue, sleep: RecordingSleep
) -> None:
    with pytest.raises(LeadNotFound):
        await _enrich(repo, queue, FakeLLMProvider(), sleep).execute(LeadId.new())
