"""Task 2.4 — port protocols and their DTOs."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.enrichment import Enrichment
from app.domain.lead import Lead
from app.domain.lead_aggregate import LeadAggregate
from app.domain.ports import (
    CrmGateway,
    LeadAnalysis,
    LeadRepository,
    LLMProvider,
    Task,
    TaskKind,
    TaskQueue,
)
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score
from app.domain.sync_state import SyncState
from app.domain.value_objects import CrmContactId, Email, LeadId, TaskId


def _analysis() -> LeadAnalysis:
    return LeadAnalysis(
        enrichment=Enrichment(
            industry="saas",
            company_size_band="11-50",
            seniority="founder",
            intent_signals=("demo",),
        ),
        score=Score.create(88, "great fit"),
        reply_draft=ReplyDraft(subject="Hi", body="Hello there"),
    )


def test_task_kinds() -> None:
    assert {TaskKind.ENRICH, TaskKind.SYNC} == set(TaskKind)


def test_lead_analysis_bundles_the_trio() -> None:
    analysis = _analysis()
    assert analysis.score.value == 88
    assert analysis.reply_draft.subject == "Hi"
    assert analysis.enrichment.industry == "saas"


def test_task_dto_is_a_frozen_record() -> None:
    task = Task(id=TaskId.new(), lead_id=LeadId.new(), kind=TaskKind.ENRICH, attempts=0)
    assert task.kind is TaskKind.ENRICH
    assert task.attempts == 0


class _FakeEverything:
    async def analyze(self, lead: Lead) -> LeadAnalysis:
        return _analysis()

    async def upsert_contact(self, lead: Lead) -> CrmContactId:
        return CrmContactId("1")

    async def attach_note(self, contact_id: CrmContactId, note: str) -> None:
        return None

    async def save(self, lead: Lead) -> None:
        return None

    async def get(self, lead_id: LeadId) -> Lead | None:
        return None

    async def find_recent_duplicate(
        self, *, email: Email, source: str, since: datetime
    ) -> Lead | None:
        return None

    async def save_analysis(self, lead_id: LeadId, analysis: LeadAnalysis) -> None:
        return None

    async def save_sync_state(self, lead_id: LeadId, sync_state: SyncState) -> None:
        return None

    async def get_aggregate(self, lead_id: LeadId) -> LeadAggregate | None:
        return None

    async def list_aggregates(self, *, limit: int, offset: int) -> list[LeadAggregate]:
        return []

    async def enqueue(self, kind: TaskKind, lead_id: LeadId) -> None:
        return None

    async def claim(self, kinds: set[TaskKind]) -> Task | None:
        return None

    async def complete(self, task_id: TaskId) -> None:
        return None

    async def fail(self, task_id: TaskId, error: str, retry_in: timedelta | None) -> None:
        return None


class _MissingMethods:
    async def analyze(self, lead: Lead) -> LeadAnalysis:
        return _analysis()


def test_conforming_object_matches_every_port_shape() -> None:
    obj = _FakeEverything()
    assert isinstance(obj, LLMProvider)
    assert isinstance(obj, CrmGateway)
    assert isinstance(obj, LeadRepository)
    assert isinstance(obj, TaskQueue)


def test_partial_object_only_matches_the_port_it_satisfies() -> None:
    obj = _MissingMethods()
    assert isinstance(obj, LLMProvider)
    assert not isinstance(obj, CrmGateway)
    assert not isinstance(obj, TaskQueue)
