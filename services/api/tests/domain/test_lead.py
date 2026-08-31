"""Task 2.2 / Phase 3 refactor — Lead entity: registration + lifecycle transitions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.contact_details import ContactDetails
from app.domain.errors import InvalidLeadStatusTransition
from app.domain.lead import Lead
from app.domain.status import LeadStatus
from app.domain.value_objects import Email

T0 = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def _contact(**overrides: object) -> ContactDetails:
    kwargs: dict[str, object] = {"name": "Ada Lovelace", "email": Email("ada@example.com")}
    kwargs.update(overrides)
    return ContactDetails(**kwargs)  # type: ignore[arg-type]


def _register(*, source: str = "website-form", now: datetime = T0, **contact: object) -> Lead:
    return Lead.register(source=source, contact=_contact(**contact), now=now)


class TestRegister:
    def test_new_lead_starts_received_with_matching_timestamps(self) -> None:
        lead = _register()
        assert lead.status is LeadStatus.RECEIVED
        assert lead.created_at == lead.updated_at == T0
        assert lead.created_at.tzinfo is not None
        assert lead.failure_reason is None

    def test_wires_the_contact_and_trims_the_source(self) -> None:
        lead = _register(source="  website-form  ", company="Analytical Engines")
        assert lead.source == "website-form"
        assert lead.contact.name == "Ada Lovelace"
        assert lead.contact.company == "Analytical Engines"


class TestTransitions:
    def test_advance_follows_the_forward_path_and_bumps_updated_at(self) -> None:
        lead = _register()
        lead.advance_to(LeadStatus.ENRICHING, now=T0 + timedelta(seconds=5))
        assert lead.status is LeadStatus.ENRICHING
        assert lead.updated_at == T0 + timedelta(seconds=5)
        assert lead.created_at == T0

    def test_full_happy_chain(self) -> None:
        lead = _register()
        for target in (
            LeadStatus.ENRICHING,
            LeadStatus.QUALIFIED,
            LeadStatus.SYNCING,
            LeadStatus.SYNCED,
        ):
            lead.advance_to(target)
        assert lead.status is LeadStatus.SYNCED

    def test_illegal_transition_raises_and_leaves_status_untouched(self) -> None:
        lead = _register()
        with pytest.raises(InvalidLeadStatusTransition):
            lead.advance_to(LeadStatus.SYNCED)
        assert lead.status is LeadStatus.RECEIVED

    def test_mark_failed_records_reason(self) -> None:
        lead = _register()
        lead.advance_to(LeadStatus.ENRICHING)
        lead.mark_failed("gemini exhausted retries")
        assert lead.status is LeadStatus.FAILED
        assert lead.failure_reason == "gemini exhausted retries"

    def test_failed_lead_can_be_retried_into_enriching(self) -> None:
        lead = _register()
        lead.mark_failed("boom")
        lead.advance_to(LeadStatus.ENRICHING)
        assert lead.status is LeadStatus.ENRICHING
