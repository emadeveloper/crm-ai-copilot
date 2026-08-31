"""Accept an inbound lead: dedupe, persist as ``received``, and queue enrichment."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.domain.contact_details import ContactDetails
from app.domain.lead import Lead
from app.domain.ports import LeadRepository, TaskKind, TaskQueue
from app.domain.value_objects import LeadId

_DEFAULT_DEDUP_WINDOW = timedelta(hours=24)


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class SubmitLeadCommand:
    source: str
    contact: ContactDetails


@dataclass(frozen=True, slots=True)
class SubmitLeadResult:
    lead_id: LeadId
    deduplicated: bool


class SubmitLead:
    def __init__(
        self,
        *,
        leads: LeadRepository,
        queue: TaskQueue,
        dedup_window: timedelta = _DEFAULT_DEDUP_WINDOW,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._leads = leads
        self._queue = queue
        self._dedup_window = dedup_window
        self._clock = clock

    async def execute(self, command: SubmitLeadCommand) -> SubmitLeadResult:
        now = self._clock()
        existing = await self._leads.find_recent_duplicate(
            email=command.contact.email,
            source=command.source,
            since=now - self._dedup_window,
        )
        if existing is not None:
            return SubmitLeadResult(lead_id=existing.id, deduplicated=True)

        lead = Lead.register(source=command.source, contact=command.contact, now=now)
        await self._leads.save(lead)
        await self._queue.enqueue(TaskKind.ENRICH, lead.id)
        return SubmitLeadResult(lead_id=lead.id, deduplicated=False)
