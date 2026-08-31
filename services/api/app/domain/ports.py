"""The ports the domain depends on. Adapters live outside and implement these structurally.

Nothing here imports a framework or a vendor SDK — that is the hexagonal boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.domain.enrichment import Enrichment
from app.domain.lead import Lead
from app.domain.lead_aggregate import LeadAggregate
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score
from app.domain.sync_state import SyncState
from app.domain.value_objects import CrmContactId, Email, LeadId, TaskId


class TaskKind(StrEnum):
    ENRICH = "enrich"
    SYNC = "sync"


@dataclass(frozen=True, slots=True)
class Task:
    id: TaskId
    lead_id: LeadId
    kind: TaskKind
    attempts: int


@dataclass(frozen=True, slots=True)
class LeadAnalysis:
    """The complete output of one LLM pass over a lead."""

    enrichment: Enrichment
    score: Score
    reply_draft: ReplyDraft


@runtime_checkable
class LLMProvider(Protocol):
    async def analyze(self, lead: Lead) -> LeadAnalysis: ...


@runtime_checkable
class CrmGateway(Protocol):
    async def upsert_contact(self, lead: Lead) -> CrmContactId: ...

    async def attach_note(self, contact_id: CrmContactId, note: str) -> None: ...


@runtime_checkable
class LeadRepository(Protocol):
    async def save(self, lead: Lead) -> None: ...

    async def get(self, lead_id: LeadId) -> Lead | None: ...

    async def find_recent_duplicate(
        self, *, email: Email, source: str, since: datetime
    ) -> Lead | None: ...

    async def save_analysis(self, lead_id: LeadId, analysis: LeadAnalysis) -> None: ...

    async def save_sync_state(self, lead_id: LeadId, sync_state: SyncState) -> None: ...

    async def get_aggregate(self, lead_id: LeadId) -> LeadAggregate | None: ...

    async def list_aggregates(self, *, limit: int, offset: int) -> list[LeadAggregate]: ...


@runtime_checkable
class TaskQueue(Protocol):
    async def enqueue(self, kind: TaskKind, lead_id: LeadId) -> None: ...

    async def claim(self, kinds: set[TaskKind]) -> Task | None: ...

    async def complete(self, task_id: TaskId) -> None: ...

    async def fail(self, task_id: TaskId, error: str, retry_in: timedelta | None) -> None: ...
