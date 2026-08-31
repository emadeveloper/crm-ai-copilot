"""Task 2.2 — Enrichment, ReplyDraft, SyncState."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.enrichment import Enrichment
from app.domain.errors import InvalidReplyDraft
from app.domain.reply_draft import ReplyDraft
from app.domain.sync_state import SyncState, SyncStatus
from app.domain.value_objects import CrmContactId

AT = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


class TestEnrichment:
    def test_stores_intent_signals_as_an_immutable_tuple(self) -> None:
        enrichment = Enrichment(
            industry="fintech",
            company_size_band="51-200",
            seniority="c-level",
            intent_signals=("asked about pricing", "booked a demo"),
        )
        assert enrichment.intent_signals == ("asked about pricing", "booked a demo")
        assert isinstance(enrichment.intent_signals, tuple)

    def test_allows_unknown_fields_to_be_none_with_no_signals(self) -> None:
        enrichment = Enrichment(
            industry=None, company_size_band=None, seniority=None, intent_signals=()
        )
        assert enrichment.intent_signals == ()
        assert enrichment.industry is None


class TestReplyDraft:
    def test_holds_subject_and_body(self) -> None:
        draft = ReplyDraft(subject="Thanks for reaching out", body="Hi Ada, happy to help...")
        assert draft.subject == "Thanks for reaching out"
        assert draft.body.startswith("Hi Ada")

    @pytest.mark.parametrize(("subject", "body"), [("", "x"), ("x", "   "), ("  ", "  ")])
    def test_rejects_blank_subject_or_body(self, subject: str, body: str) -> None:
        with pytest.raises(InvalidReplyDraft):
            ReplyDraft(subject=subject, body=body)


class TestSyncState:
    def test_pending_is_the_starting_point(self) -> None:
        state = SyncState.pending()
        assert state.status is SyncStatus.PENDING
        assert state.crm_contact_id is None
        assert state.synced_at is None
        assert state.failure_reason is None

    def test_mark_synced_records_the_contact_and_timestamp(self) -> None:
        state = SyncState.pending()
        state.mark_synced(CrmContactId("501"), at=AT)
        assert state.status is SyncStatus.SYNCED
        assert state.crm_contact_id == CrmContactId("501")
        assert state.synced_at == AT
        assert state.failure_reason is None

    def test_mark_failed_keeps_a_previously_known_contact_id(self) -> None:
        state = SyncState.pending()
        state.mark_synced(CrmContactId("501"), at=AT)
        state.mark_failed("hubspot 429 on note create")
        assert state.status is SyncStatus.FAILED
        assert state.failure_reason == "hubspot 429 on note create"
        assert state.crm_contact_id == CrmContactId("501")

    def test_mark_failed_from_pending_has_no_contact_id(self) -> None:
        state = SyncState.pending()
        state.mark_failed("auth error")
        assert state.status is SyncStatus.FAILED
        assert state.crm_contact_id is None
        assert state.failure_reason == "auth error"
