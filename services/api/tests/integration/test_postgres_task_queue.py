"""Task 4.2 — PostgresTaskQueue against a real PostgreSQL (spec: lead-pipeline)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence.repository import SqlLeadRepository
from app.adapters.queue.postgres import PostgresTaskQueue
from app.domain.contact_details import ContactDetails
from app.domain.lead import Lead
from app.domain.ports import TaskKind
from app.domain.value_objects import Email, LeadId

BASE = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


@pytest_asyncio.fixture
async def lead_id(sessionmaker: async_sessionmaker[AsyncSession]) -> LeadId:
    lead = Lead.register(
        source="form",
        contact=ContactDetails(name="Ada", email=Email("ada@example.com")),
        now=BASE,
    )
    await SqlLeadRepository(sessionmaker).save(lead)
    return lead.id


@pytest_asyncio.fixture
async def queue(sessionmaker: async_sessionmaker[AsyncSession]) -> PostgresTaskQueue:
    return PostgresTaskQueue(sessionmaker, worker_id="test-worker")


async def test_enqueue_then_claim_returns_the_task_and_increments_attempts(
    queue: PostgresTaskQueue, lead_id: LeadId
) -> None:
    await queue.enqueue(TaskKind.ENRICH, lead_id)

    task = await queue.claim({TaskKind.ENRICH})
    assert task is not None
    assert task.lead_id == lead_id
    assert task.kind is TaskKind.ENRICH
    assert task.attempts == 1

    assert await queue.claim({TaskKind.ENRICH}) is None  # already in progress


async def test_claim_ignores_other_kinds(queue: PostgresTaskQueue, lead_id: LeadId) -> None:
    await queue.enqueue(TaskKind.ENRICH, lead_id)
    assert await queue.claim({TaskKind.SYNC}) is None
    assert await queue.claim({TaskKind.ENRICH, TaskKind.SYNC}) is not None


async def test_complete_removes_the_task_from_the_queue(
    queue: PostgresTaskQueue, lead_id: LeadId
) -> None:
    await queue.enqueue(TaskKind.ENRICH, lead_id)
    task = await queue.claim({TaskKind.ENRICH})
    assert task is not None

    await queue.complete(task.id)
    assert await queue.claim({TaskKind.ENRICH}) is None


async def test_fail_with_retry_reschedules_the_task(
    queue: PostgresTaskQueue, lead_id: LeadId
) -> None:
    await queue.enqueue(TaskKind.ENRICH, lead_id)
    task = await queue.claim({TaskKind.ENRICH})
    assert task is not None

    await queue.fail(task.id, "boom", retry_in=timedelta(seconds=-1))  # due immediately

    retried = await queue.claim({TaskKind.ENRICH})
    assert retried is not None
    assert retried.id == task.id
    assert retried.attempts == 2


async def test_fail_without_retry_parks_the_task(queue: PostgresTaskQueue, lead_id: LeadId) -> None:
    await queue.enqueue(TaskKind.ENRICH, lead_id)
    task = await queue.claim({TaskKind.ENRICH})
    assert task is not None

    await queue.fail(task.id, "exhausted", retry_in=None)
    assert await queue.claim({TaskKind.ENRICH}) is None


async def test_stale_in_progress_task_is_reclaimed_after_restart(
    sessionmaker: async_sessionmaker[AsyncSession], lead_id: LeadId
) -> None:
    queue = PostgresTaskQueue(sessionmaker, worker_id="w1", stale_after=timedelta(seconds=-1))
    await queue.enqueue(TaskKind.ENRICH, lead_id)
    first = await queue.claim({TaskKind.ENRICH})
    assert first is not None  # now in_progress, "locked" by a worker that then crashes

    reclaimed = await queue.claim({TaskKind.ENRICH})
    assert reclaimed is not None and reclaimed.id == first.id
    assert reclaimed.attempts == 2


async def test_concurrent_claims_never_hand_out_the_same_task(
    queue: PostgresTaskQueue, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    repo = SqlLeadRepository(sessionmaker)
    lead_ids = []
    for i in range(5):
        lead = Lead.register(
            source="form",
            contact=ContactDetails(name=f"L{i}", email=Email(f"l{i}@example.com")),
            now=BASE,
        )
        await repo.save(lead)
        lead_ids.append(lead.id)
    for lid in lead_ids:
        await queue.enqueue(TaskKind.ENRICH, lid)

    results = await asyncio.gather(*(queue.claim({TaskKind.ENRICH}) for _ in range(8)))

    claimed = [t for t in results if t is not None]
    assert len(claimed) == 5
    assert len({t.id for t in claimed}) == 5
