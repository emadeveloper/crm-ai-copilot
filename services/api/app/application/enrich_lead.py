"""Run one lead through LLM enrichment, with bounded retry on transient failures."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from app.application.errors import LLMResponseInvalid, LLMTemporaryError
from app.domain.errors import LeadNotFound
from app.domain.ports import LeadRepository, LLMProvider, TaskKind, TaskQueue
from app.domain.status import LeadStatus
from app.domain.value_objects import LeadId

_DEFAULT_MAX_ATTEMPTS = 5
_DEFAULT_BACKOFF_BASE = timedelta(seconds=2)
_ENRICHABLE = (LeadStatus.RECEIVED, LeadStatus.ENRICHING)

Sleep = Callable[[float], Awaitable[None]]


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def _real_sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


class EnrichLead:
    def __init__(
        self,
        *,
        leads: LeadRepository,
        queue: TaskQueue,
        llm: LLMProvider,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        backoff_base: timedelta = _DEFAULT_BACKOFF_BASE,
        sleep: Sleep = _real_sleep,
        clock: Callable[[], datetime] = _utcnow,
        sync_enabled: bool = True,
    ) -> None:
        self._leads = leads
        self._queue = queue
        self._llm = llm
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base.total_seconds()
        self._sleep = sleep
        self._clock = clock
        self._sync_enabled = sync_enabled

    async def execute(self, lead_id: LeadId) -> None:
        lead = await self._leads.get(lead_id)
        if lead is None:
            raise LeadNotFound(str(lead_id))
        if lead.status not in _ENRICHABLE:
            return  # already past enrichment — nothing to do

        if lead.status is LeadStatus.RECEIVED:
            lead.advance_to(LeadStatus.ENRICHING, now=self._clock())
            await self._leads.save(lead)

        analysis = None
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                analysis = await self._llm.analyze(lead)
                break
            except LLMResponseInvalid as exc:
                last_error = exc
                break  # deterministic bad response — retrying will not help
            except LLMTemporaryError as exc:
                last_error = exc
                if attempt < self._max_attempts:
                    await self._sleep(self._backoff_base * 2 ** (attempt - 1))

        if analysis is None:
            lead.mark_failed(f"enrichment failed: {last_error}", now=self._clock())
            await self._leads.save(lead)
            return

        await self._leads.save_analysis(lead_id, analysis)
        lead.advance_to(LeadStatus.QUALIFIED, now=self._clock())
        await self._leads.save(lead)
        if self._sync_enabled:
            await self._queue.enqueue(TaskKind.SYNC, lead_id)
