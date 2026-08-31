"""The pipeline worker: drain the task queue, running enrichment then CRM sync.

Runs in-process (started on API startup) and is also launchable standalone via
``python -m app.worker``. Because claiming uses ``FOR UPDATE SKIP LOCKED`` and a stale-lock
reclaim, several instances can run at once.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import timedelta
from typing import Protocol

from app.domain.ports import TaskKind, TaskQueue
from app.domain.value_objects import LeadId

logger = logging.getLogger("app.worker")


class LeadTaskHandler(Protocol):
    """A use case the worker can dispatch a task to (EnrichLead, SyncLeadToCrm)."""

    async def execute(self, lead_id: LeadId) -> None: ...


_KINDS = {TaskKind.ENRICH, TaskKind.SYNC}
_DEFAULT_POLL = 2.0
_DEFAULT_BACKOFF_BASE = timedelta(seconds=5)


class PipelineWorker:
    def __init__(
        self,
        *,
        queue: TaskQueue,
        enrich: LeadTaskHandler,
        sync: LeadTaskHandler,
        max_attempts: int,
        poll_interval: float = _DEFAULT_POLL,
        backoff_base: timedelta = _DEFAULT_BACKOFF_BASE,
    ) -> None:
        self._queue = queue
        self._enrich = enrich
        self._sync = sync
        self._max_attempts = max_attempts
        self._poll_interval = poll_interval
        self._backoff_base = backoff_base.total_seconds()

    async def run_once(self) -> bool:
        """Process at most one task. Returns True if a task was picked up."""
        task = await self._queue.claim(_KINDS)
        if task is None:
            return False
        try:
            if task.kind is TaskKind.ENRICH:
                await self._enrich.execute(task.lead_id)
            else:
                await self._sync.execute(task.lead_id)
        except Exception as exc:  # worker must not die on one bad task
            retry_in = (
                None
                if task.attempts >= self._max_attempts
                else timedelta(seconds=self._backoff_base * 2 ** (task.attempts - 1))
            )
            logger.warning(
                "task %s (%s) failed on attempt %s: %s", task.id, task.kind, task.attempts, exc
            )
            await self._queue.fail(task.id, str(exc), retry_in=retry_in)
        else:
            await self._queue.complete(task.id)
        return True

    async def run_forever(self, *, stop: asyncio.Event) -> None:
        logger.info("pipeline worker started")
        while not stop.is_set():
            try:
                processed = await self.run_once()
            except Exception:
                logger.exception("worker loop error")
                processed = False
            if not processed:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=self._poll_interval)
        logger.info("pipeline worker stopped")
