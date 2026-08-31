"""Task 3.3 — SyncLeadToCrm use case (spec: crm-sync)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.application.errors import CrmError, LeadNotReadyForSync
from app.application.sync_lead_to_crm import SyncLeadToCrm
from app.domain.contact_details import ContactDetails
from app.domain.errors import LeadNotFound
from app.domain.lead import Lead
from app.domain.status import LeadStatus
from app.domain.sync_state import SyncStatus
from app.domain.value_objects import Email, LeadId
from tests.fakes import (
    FakeCrmGateway,
    InMemoryLeadRepository,
    fixed_clock,
    sample_analysis,
)

NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


async def _qualified_lead(repo: InMemoryLeadRepository, *, email: str = "ada@example.com") -> Lead:
    lead = Lead.register(
        source="website-form",
        contact=ContactDetails(name="Ada Lovelace", email=Email(email), company="Analytical"),
        now=NOW,
    )
    lead.advance_to(LeadStatus.ENRICHING, now=NOW)
    lead.advance_to(LeadStatus.QUALIFIED, now=NOW)
    await repo.save(lead)
    await repo.save_analysis(lead.id, sample_analysis())
    return lead


@pytest.fixture
def repo() -> InMemoryLeadRepository:
    return InMemoryLeadRepository()


def _sync(repo: InMemoryLeadRepository, crm: FakeCrmGateway) -> SyncLeadToCrm:
    return SyncLeadToCrm(leads=repo, crm=crm, clock=fixed_clock(NOW))


async def test_creates_a_contact_attaches_a_note_and_marks_synced(
    repo: InMemoryLeadRepository,
) -> None:
    lead = await _qualified_lead(repo)
    crm = FakeCrmGateway()

    await _sync(repo, crm).execute(lead.id)

    assert crm.upsert_calls == 1
    assert len(crm.notes) == 1
    _, note_body = crm.notes[0]
    assert "82" in note_body and "Enterprise buyer" in note_body
    assert "Thanks for reaching out" in note_body

    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None
    assert aggregate.lead.status is LeadStatus.SYNCED
    assert aggregate.sync_state is not None
    assert aggregate.sync_state.status is SyncStatus.SYNCED
    assert aggregate.sync_state.crm_contact_id is not None
    assert aggregate.sync_state.synced_at == NOW


async def test_existing_hubspot_contact_is_updated_not_duplicated(
    repo: InMemoryLeadRepository,
) -> None:
    lead = await _qualified_lead(repo, email="known@corp.com")
    crm = FakeCrmGateway(existing={"known@corp.com": "999"})

    await _sync(repo, crm).execute(lead.id)

    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None and aggregate.sync_state is not None
    assert str(aggregate.sync_state.crm_contact_id) == "999"
    assert crm.notes[0][0].value == "999"


async def test_resync_reuses_the_stored_contact_id_without_calling_upsert(
    repo: InMemoryLeadRepository,
) -> None:
    lead = await _qualified_lead(repo)
    crm = FakeCrmGateway()
    await _sync(repo, crm).execute(lead.id)  # first sync
    first_contact = (await repo.get_aggregate(lead.id)).sync_state.crm_contact_id  # type: ignore[union-attr]

    crm2 = FakeCrmGateway()
    await _sync(repo, crm2).execute(lead.id)  # re-sync

    assert crm2.upsert_calls == 0
    assert crm2.notes[0][0] == first_contact


async def test_gateway_failure_on_upsert_records_failed_state_and_keeps_derived_data(
    repo: InMemoryLeadRepository,
) -> None:
    lead = await _qualified_lead(repo)
    crm = FakeCrmGateway(fail_on="upsert")

    with pytest.raises(CrmError):
        await _sync(repo, crm).execute(lead.id)

    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None and aggregate.sync_state is not None
    assert aggregate.sync_state.status is SyncStatus.FAILED
    assert aggregate.sync_state.failure_reason is not None
    assert aggregate.sync_state.crm_contact_id is None
    assert aggregate.lead.status is LeadStatus.SYNCING  # still retry-eligible
    assert aggregate.score is not None and aggregate.reply_draft is not None


async def test_gateway_failure_on_note_keeps_the_discovered_contact_id_for_retry(
    repo: InMemoryLeadRepository,
) -> None:
    lead = await _qualified_lead(repo)
    crm = FakeCrmGateway(fail_on="note")

    with pytest.raises(CrmError):
        await _sync(repo, crm).execute(lead.id)

    aggregate = await repo.get_aggregate(lead.id)
    assert aggregate is not None and aggregate.sync_state is not None
    assert aggregate.sync_state.status is SyncStatus.FAILED
    assert aggregate.sync_state.crm_contact_id is not None


async def test_lead_without_score_or_draft_raises(repo: InMemoryLeadRepository) -> None:
    lead = Lead.register(
        source="form",
        contact=ContactDetails(name="Ada", email=Email("ada@example.com")),
        now=NOW,
    )
    lead.advance_to(LeadStatus.ENRICHING, now=NOW)
    lead.advance_to(LeadStatus.QUALIFIED, now=NOW)
    await repo.save(lead)

    with pytest.raises(LeadNotReadyForSync):
        await _sync(repo, FakeCrmGateway()).execute(lead.id)


async def test_unknown_lead_raises(repo: InMemoryLeadRepository) -> None:
    with pytest.raises(LeadNotFound):
        await _sync(repo, FakeCrmGateway()).execute(LeadId.new())
