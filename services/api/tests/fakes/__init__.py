"""In-memory fakes for the four domain ports. Used by application-layer unit tests.

Formalised in Phase 7 (task 7.1); created early because the Phase 3 use-case tests need them.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.application.errors import CrmError, LLMTemporaryError
from app.domain.enrichment import Enrichment
from app.domain.lead import Lead
from app.domain.lead_aggregate import LeadAggregate
from app.domain.ports import LeadAnalysis, Task, TaskKind
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score
from app.domain.sync_state import SyncState
from app.domain.value_objects import CrmContactId, Email, LeadId, TaskId


def sample_analysis() -> LeadAnalysis:
    return LeadAnalysis(
        enrichment=Enrichment(
            industry="fintech",
            company_size_band="51-200",
            seniority="c-level",
            intent_signals=("asked about pricing",),
        ),
        score=Score.create(82, "Enterprise buyer, explicit budget"),
        reply_draft=ReplyDraft(subject="Thanks for reaching out", body="Hi, happy to help..."),
    )


class InMemoryLeadRepository:
    """Stores deep copies so callers only see state that was explicitly saved."""

    def __init__(self) -> None:
        self._leads: dict[UUID, Lead] = {}
        self._analyses: dict[UUID, LeadAnalysis] = {}
        self._sync: dict[UUID, SyncState] = {}

    async def save(self, lead: Lead) -> None:
        self._leads[lead.id.value] = copy.deepcopy(lead)

    async def get(self, lead_id: LeadId) -> Lead | None:
        stored = self._leads.get(lead_id.value)
        return copy.deepcopy(stored) if stored is not None else None

    async def find_recent_duplicate(
        self, *, email: Email, source: str, since: datetime
    ) -> Lead | None:
        for lead in self._leads.values():
            if lead.contact.email == email and lead.source == source and lead.created_at >= since:
                return copy.deepcopy(lead)
        return None

    async def save_analysis(self, lead_id: LeadId, analysis: LeadAnalysis) -> None:
        self._analyses[lead_id.value] = analysis

    async def save_sync_state(self, lead_id: LeadId, sync_state: SyncState) -> None:
        self._sync[lead_id.value] = copy.deepcopy(sync_state)

    async def get_aggregate(self, lead_id: LeadId) -> LeadAggregate | None:
        stored = self._leads.get(lead_id.value)
        if stored is None:
            return None
        return self._aggregate_for(stored)

    async def list_aggregates(self, *, limit: int, offset: int) -> list[LeadAggregate]:
        ordered = sorted(self._leads.values(), key=lambda lead: lead.created_at, reverse=True)
        return [self._aggregate_for(lead) for lead in ordered[offset : offset + limit]]

    def _aggregate_for(self, lead: Lead) -> LeadAggregate:
        analysis = self._analyses.get(lead.id.value)
        return LeadAggregate(
            lead=copy.deepcopy(lead),
            enrichment=analysis.enrichment if analysis else None,
            score=analysis.score if analysis else None,
            reply_draft=analysis.reply_draft if analysis else None,
            sync_state=copy.deepcopy(self._sync.get(lead.id.value)),
        )


class FakeLLMProvider:
    def __init__(
        self,
        *,
        analysis: LeadAnalysis | None = None,
        fail_times: int = 0,
        error: Exception | None = None,
    ) -> None:
        self._analysis = analysis or sample_analysis()
        self._fail_times = fail_times
        self._error = error or LLMTemporaryError("simulated rate limit")
        self.calls = 0

    async def analyze(self, lead: Lead) -> LeadAnalysis:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise self._error
        return self._analysis


class FakeCrmGateway:
    def __init__(
        self,
        *,
        existing: dict[str, str] | None = None,
        fail_on: str | None = None,
    ) -> None:
        self._contacts: dict[str, CrmContactId] = {
            email: CrmContactId(cid) for email, cid in (existing or {}).items()
        }
        self._fail_on = fail_on  # "upsert" | "note" | None
        self._seq = 1000
        self.upsert_calls = 0
        self.notes: list[tuple[CrmContactId, str]] = []

    async def upsert_contact(self, lead: Lead) -> CrmContactId:
        if self._fail_on == "upsert":
            raise CrmError("hubspot authentication failed")
        self.upsert_calls += 1
        key = str(lead.contact.email)
        if key not in self._contacts:
            self._seq += 1
            self._contacts[key] = CrmContactId(str(self._seq))
        return self._contacts[key]

    async def attach_note(self, contact_id: CrmContactId, note: str) -> None:
        if self._fail_on == "note":
            raise CrmError("hubspot 429 on note create")
        self.notes.append((contact_id, note))


class InMemoryTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[tuple[TaskKind, LeadId]] = []
        self._pending: list[Task] = []
        self.completed: list[TaskId] = []
        self.failed: list[tuple[TaskId, str, timedelta | None]] = []

    async def enqueue(self, kind: TaskKind, lead_id: LeadId) -> None:
        self.enqueued.append((kind, lead_id))
        self._pending.append(Task(id=TaskId.new(), lead_id=lead_id, kind=kind, attempts=0))

    async def claim(self, kinds: set[TaskKind]) -> Task | None:
        for index, task in enumerate(self._pending):
            if task.kind in kinds:
                self._pending.pop(index)
                # Mirror PostgresTaskQueue: claiming increments the attempt counter.
                return Task(
                    id=task.id,
                    lead_id=task.lead_id,
                    kind=task.kind,
                    attempts=task.attempts + 1,
                )
        return None

    async def complete(self, task_id: TaskId) -> None:
        self.completed.append(task_id)

    async def fail(self, task_id: TaskId, error: str, retry_in: timedelta | None) -> None:
        self.failed.append((task_id, error, retry_in))


class RecordingSleep:
    """Stand-in for asyncio.sleep that records durations instead of waiting."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def fixed_clock(at: datetime) -> Callable[[], datetime]:
    return lambda: at


__all__ = [
    "UTC",
    "FakeCrmGateway",
    "FakeLLMProvider",
    "InMemoryLeadRepository",
    "InMemoryTaskQueue",
    "RecordingSleep",
    "fixed_clock",
    "sample_analysis",
]
