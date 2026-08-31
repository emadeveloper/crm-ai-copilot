"""Task 4.1 — pure domain <-> ORM row mappers (no database)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.adapters.persistence import mappers
from app.domain.contact_details import ContactDetails
from app.domain.enrichment import Enrichment
from app.domain.lead import Lead
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score, ScoreBand
from app.domain.status import LeadStatus
from app.domain.sync_state import SyncState, SyncStatus
from app.domain.value_objects import CrmContactId, Email

T0 = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def _lead() -> Lead:
    return Lead.register(
        source="website-form",
        contact=ContactDetails(
            name="Ada Lovelace",
            email=Email("ada@example.com"),
            company="Analytical Engines",
            role="CTO",
            message="pricing?",
        ),
        now=T0,
    )


class TestLeadMapper:
    def test_round_trips_all_fields(self) -> None:
        original = _lead()
        original.advance_to(LeadStatus.ENRICHING, now=T0)

        restored = mappers.row_to_lead(mappers.lead_to_row(original))

        assert restored.id == original.id
        assert restored.source == "website-form"
        assert restored.contact == original.contact
        assert restored.status is LeadStatus.ENRICHING
        assert restored.created_at == T0

    def test_maps_failure_reason(self) -> None:
        lead = _lead()
        lead.mark_failed("boom", now=T0)
        restored = mappers.row_to_lead(mappers.lead_to_row(lead))
        assert restored.status is LeadStatus.FAILED
        assert restored.failure_reason == "boom"


class TestAnalysisMappers:
    def test_enrichment_round_trip(self) -> None:
        enrichment = Enrichment(
            industry="fintech",
            company_size_band="51-200",
            seniority="c-level",
            intent_signals=("asked about pricing", "booked a demo"),
        )
        row = mappers.enrichment_to_row(_lead().id, enrichment)
        assert mappers.row_to_enrichment(row) == enrichment

    def test_enrichment_round_trip_with_nulls(self) -> None:
        enrichment = Enrichment(
            industry=None, company_size_band=None, seniority=None, intent_signals=()
        )
        row = mappers.enrichment_to_row(_lead().id, enrichment)
        assert mappers.row_to_enrichment(row) == enrichment

    def test_score_round_trip(self) -> None:
        score = Score(value=82, band=ScoreBand.HOT, rationale="enterprise buyer")
        row = mappers.score_to_row(_lead().id, score)
        assert mappers.row_to_score(row) == score

    def test_reply_draft_round_trip(self) -> None:
        draft = ReplyDraft(subject="Hi there", body="Thanks for reaching out")
        row = mappers.reply_draft_to_row(_lead().id, draft)
        assert mappers.row_to_reply_draft(row) == draft


class TestSyncStateMapper:
    def test_round_trips_a_synced_state(self) -> None:
        state = SyncState.pending()
        state.mark_synced(CrmContactId("501"), at=T0)
        row = mappers.sync_state_to_row(_lead().id, state)
        restored = mappers.row_to_sync_state(row)
        assert restored.status is SyncStatus.SYNCED
        assert restored.crm_contact_id == CrmContactId("501")
        assert restored.synced_at == T0

    def test_round_trips_a_failed_state_keeping_contact_id(self) -> None:
        state = SyncState.pending()
        state.mark_synced(CrmContactId("501"), at=T0)
        state.mark_failed("429 on note")
        restored = mappers.row_to_sync_state(mappers.sync_state_to_row(_lead().id, state))
        assert restored.status is SyncStatus.FAILED
        assert restored.failure_reason == "429 on note"
        assert restored.crm_contact_id == CrmContactId("501")
