"""Task 5.4 — PipelineWorker (spec: lead-pipeline)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest

from app.domain.ports import TaskKind
from app.domain.value_objects import LeadId
from app.infra.worker import PipelineWorker
from tests.fakes import InMemoryTaskQueue


class _Recorder:
    def __init__(self, *, fail_with: Exception | None = None) -> None:
        self.calls: list[LeadId] = []
        self._fail_with = fail_with

    async def execute(self, lead_id: LeadId) -> None:
        self.calls.append(lead_id)
        if self._fail_with is not None:
            raise self._fail_with


def _worker(
    queue: InMemoryTaskQueue,
    *,
    enrich: _Recorder | None = None,
    sync: _Recorder | None = None,
    max_attempts: int = 3,
) -> PipelineWorker:
    return PipelineWorker(
        queue=queue,
        enrich=enrich or _Recorder(),
        sync=sync or _Recorder(),
        max_attempts=max_attempts,
        poll_interval=0.01,
        backoff_base=timedelta(seconds=4),
    )


async def test_run_once_on_empty_queue_returns_false() -> None:
    assert await _worker(InMemoryTaskQueue()).run_once() is False


async def test_run_once_dispatches_enrich_and_completes() -> None:
    queue = InMemoryTaskQueue()
    lead_id = LeadId.new()
    await queue.enqueue(TaskKind.ENRICH, lead_id)
    enrich = _Recorder()

    handled = await _worker(queue, enrich=enrich).run_once()

    assert handled is True
    assert enrich.calls == [lead_id]
    assert len(queue.completed) == 1
    assert queue.failed == []


async def test_run_once_dispatches_sync() -> None:
    queue = InMemoryTaskQueue()
    lead_id = LeadId.new()
    await queue.enqueue(TaskKind.SYNC, lead_id)
    sync = _Recorder()

    await _worker(queue, sync=sync).run_once()

    assert sync.calls == [lead_id]
    assert len(queue.completed) == 1


async def test_failure_below_max_attempts_reschedules_with_backoff() -> None:
    queue = InMemoryTaskQueue()
    await queue.enqueue(TaskKind.ENRICH, LeadId.new())
    # claim once so the task's attempts becomes 1 before the worker sees it again
    enrich = _Recorder(fail_with=RuntimeError("crm down"))

    await _worker(queue, enrich=enrich, max_attempts=3).run_once()

    assert queue.completed == []
    assert len(queue.failed) == 1
    _, error, retry_in = queue.failed[0]
    assert "crm down" in error
    assert retry_in == timedelta(seconds=4)  # base * 2**(attempts-1), attempts == 1


async def test_failure_at_max_attempts_parks_the_task() -> None:
    queue = InMemoryTaskQueue()
    await queue.enqueue(TaskKind.ENRICH, LeadId.new())
    enrich = _Recorder(fail_with=RuntimeError("still down"))

    await _worker(queue, enrich=enrich, max_attempts=1).run_once()

    assert queue.failed[0][2] is None  # retry_in None -> parked


async def test_run_forever_drains_then_stops_promptly() -> None:
    queue = InMemoryTaskQueue()
    for _ in range(3):
        await queue.enqueue(TaskKind.ENRICH, LeadId.new())
    enrich = _Recorder()
    worker = _worker(queue, enrich=enrich)
    stop = asyncio.Event()

    run = asyncio.create_task(worker.run_forever(stop=stop))
    await asyncio.sleep(0.1)  # ample time for three ~instant tasks
    stop.set()
    await asyncio.wait_for(run, timeout=2.0)

    assert len(enrich.calls) == 3
    assert len(queue.completed) == 3


@pytest.mark.parametrize("kind", [TaskKind.ENRICH, TaskKind.SYNC])
async def test_bad_task_does_not_kill_the_loop(kind: TaskKind) -> None:
    queue = InMemoryTaskQueue()
    await queue.enqueue(kind, LeadId.new())
    handler = _Recorder(fail_with=ValueError("boom"))
    worker = _worker(queue, enrich=handler, sync=handler)

    # Should not raise.
    assert await worker.run_once() is True
