"""Task 3.4 — GetLead and ListLeads use cases (spec: lead-api / retrieval)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.get_lead import GetLead
from app.application.list_leads import ListLeads
from app.domain.contact_details import ContactDetails
from app.domain.errors import LeadNotFound
from app.domain.lead import Lead
from app.domain.value_objects import Email, LeadId
from tests.fakes import InMemoryLeadRepository, sample_analysis

BASE = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


async def _make_lead(repo: InMemoryLeadRepository, *, created_at: datetime, name: str) -> Lead:
    lead = Lead.register(
        source="website-form",
        contact=ContactDetails(name=name, email=Email(f"{name.lower()}@example.com")),
        now=created_at,
    )
    await repo.save(lead)
    return lead


@pytest.fixture
def repo() -> InMemoryLeadRepository:
    return InMemoryLeadRepository()


class TestGetLead:
    async def test_returns_the_aggregate_with_derived_data(
        self, repo: InMemoryLeadRepository
    ) -> None:
        lead = await _make_lead(repo, created_at=BASE, name="Ada")
        await repo.save_analysis(lead.id, sample_analysis())

        aggregate = await GetLead(leads=repo).execute(lead.id)

        assert aggregate.lead.id == lead.id
        assert aggregate.score is not None and aggregate.score.value == 82
        assert aggregate.reply_draft is not None

    async def test_unknown_id_raises(self, repo: InMemoryLeadRepository) -> None:
        with pytest.raises(LeadNotFound):
            await GetLead(leads=repo).execute(LeadId.new())


class TestListLeads:
    async def test_returns_newest_first(self, repo: InMemoryLeadRepository) -> None:
        await _make_lead(repo, created_at=BASE, name="First")
        await _make_lead(repo, created_at=BASE + timedelta(minutes=1), name="Second")
        await _make_lead(repo, created_at=BASE + timedelta(minutes=2), name="Third")

        result = await ListLeads(leads=repo).execute()

        assert [a.lead.contact.name for a in result] == ["Third", "Second", "First"]

    async def test_clamps_limit_to_the_maximum(self, repo: InMemoryLeadRepository) -> None:
        for i in range(5):
            await _make_lead(repo, created_at=BASE + timedelta(minutes=i), name=f"L{i}")

        result = await ListLeads(leads=repo, default_limit=20, max_limit=3).execute(limit=100)

        assert len(result) == 3

    async def test_applies_offset_for_pagination(self, repo: InMemoryLeadRepository) -> None:
        for i in range(5):
            await _make_lead(repo, created_at=BASE + timedelta(minutes=i), name=f"L{i}")

        page = await ListLeads(leads=repo).execute(limit=2, offset=2)

        # newest-first is L4, L3, L2, L1, L0 -> offset 2 -> L2, L1
        assert [a.lead.contact.name for a in page] == ["L2", "L1"]

    async def test_uses_the_default_limit_when_none_is_given(
        self, repo: InMemoryLeadRepository
    ) -> None:
        for i in range(4):
            await _make_lead(repo, created_at=BASE + timedelta(minutes=i), name=f"L{i}")

        result = await ListLeads(leads=repo, default_limit=2).execute()

        assert len(result) == 2
