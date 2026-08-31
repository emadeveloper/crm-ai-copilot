"""Task 4.1 — SqlLeadRepository against a real PostgreSQL."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence.repository import SqlLeadRepository
from app.domain.contact_details import ContactDetails
from app.domain.enrichment import Enrichment
from app.domain.lead import Lead
from app.domain.ports import LeadAnalysis
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score
from app.domain.status import LeadStatus
from app.domain.sync_state import SyncState, SyncStatus
from app.domain.value_objects import CrmContactId, Email, LeadId

BASE = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def _lead(
    *, created_at: datetime = BASE, source: str = "website-form", email: str = "ada@example.com"
) -> Lead:
    return Lead.register(
        source=source,
        contact=ContactDetails(name="Ada Lovelace", email=Email(email), company="Analytical"),
        now=created_at,
    )


def _analysis(value: int = 82) -> LeadAnalysis:
    return LeadAnalysis(
        enrichment=Enrichment(
            industry="fintech",
            company_size_band="51-200",
            seniority="c-level",
            intent_signals=("pricing",),
        ),
        score=Score.create(value, "enterprise buyer"),
        reply_draft=ReplyDraft(subject="Hi", body="Thanks for reaching out"),
    )


@pytest_asyncio.fixture
async def repo(sessionmaker: async_sessionmaker[AsyncSession]) -> SqlLeadRepository:
    return SqlLeadRepository(sessionmaker)


async def test_save_then_get_round_trips(repo: SqlLeadRepository) -> None:
    lead = _lead()
    await repo.save(lead)

    fetched = await repo.get(lead.id)
    assert fetched is not None
    assert fetched.id == lead.id
    assert fetched.contact == lead.contact
    assert fetched.status is LeadStatus.RECEIVED
    assert fetched.created_at == BASE


async def test_save_is_an_upsert_not_a_duplicate(repo: SqlLeadRepository) -> None:
    lead = _lead()
    await repo.save(lead)
    lead.advance_to(LeadStatus.ENRICHING, now=BASE + timedelta(seconds=1))
    await repo.save(lead)

    fetched = await repo.get(lead.id)
    assert fetched is not None and fetched.status is LeadStatus.ENRICHING
    page = await repo.list_aggregates(limit=10, offset=0)
    assert len(page) == 1


async def test_get_unknown_returns_none(repo: SqlLeadRepository) -> None:
    assert await repo.get(LeadId.new()) is None
    assert await repo.get_aggregate(LeadId.new()) is None


async def test_find_recent_duplicate_matches_email_and_source_within_window(
    repo: SqlLeadRepository,
) -> None:
    lead = _lead(created_at=BASE)
    await repo.save(lead)

    hit = await repo.find_recent_duplicate(
        email=Email("ada@example.com"), source="website-form", since=BASE - timedelta(hours=1)
    )
    assert hit is not None and hit.id == lead.id

    other_source = await repo.find_recent_duplicate(
        email=Email("ada@example.com"), source="linkedin", since=BASE - timedelta(hours=1)
    )
    assert other_source is None

    too_old = await repo.find_recent_duplicate(
        email=Email("ada@example.com"), source="website-form", since=BASE + timedelta(hours=1)
    )
    assert too_old is None


async def test_save_analysis_persists_and_replaces(repo: SqlLeadRepository) -> None:
    lead = _lead()
    await repo.save(lead)

    await repo.save_analysis(lead.id, _analysis(value=40))
    await repo.save_analysis(lead.id, _analysis(value=90))  # replace

    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None
    assert aggregate.score is not None and aggregate.score.value == 90
    assert aggregate.enrichment is not None and aggregate.enrichment.industry == "fintech"
    assert aggregate.reply_draft is not None and aggregate.reply_draft.subject == "Hi"


async def test_save_sync_state_round_trips(repo: SqlLeadRepository) -> None:
    lead = _lead()
    await repo.save(lead)
    state = SyncState.pending()
    state.mark_synced(CrmContactId("501"), at=BASE)
    await repo.save_sync_state(lead.id, state)

    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None and aggregate.sync_state is not None
    assert aggregate.sync_state.status is SyncStatus.SYNCED
    assert aggregate.sync_state.crm_contact_id == CrmContactId("501")


async def test_list_aggregates_is_newest_first_with_limit_offset_and_matched_parts(
    repo: SqlLeadRepository,
) -> None:
    first = _lead(created_at=BASE, email="first@x.com")
    second = _lead(created_at=BASE + timedelta(minutes=1), email="second@x.com")
    third = _lead(created_at=BASE + timedelta(minutes=2), email="third@x.com")
    for lead in (first, second, third):
        await repo.save(lead)
    await repo.save_analysis(second.id, _analysis(value=77))

    page = await repo.list_aggregates(limit=2, offset=0)
    assert [a.lead.id for a in page] == [third.id, second.id]
    assert page[0].score is None
    assert page[1].score is not None and page[1].score.value == 77

    tail = await repo.list_aggregates(limit=2, offset=2)
    assert [a.lead.id for a in tail] == [first.id]


async def test_list_aggregates_handles_an_empty_table(repo: SqlLeadRepository) -> None:
    assert await repo.list_aggregates(limit=10, offset=0) == []
