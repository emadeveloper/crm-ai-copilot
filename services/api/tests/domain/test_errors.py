"""Task 2.3 — domain error hierarchy."""

from __future__ import annotations

import pytest

from app.domain.errors import (
    DomainError,
    InvalidEmail,
    InvalidLeadStatusTransition,
    InvalidReplyDraft,
    InvalidScore,
    LeadNotFound,
    ValidationError,
)


@pytest.mark.parametrize(
    "exc",
    [
        InvalidLeadStatusTransition("synced", "enriching"),
        InvalidEmail("nope"),
        InvalidScore("out of range"),
        InvalidReplyDraft("blank body"),
        LeadNotFound("11111111-1111-1111-1111-111111111111"),
    ],
)
def test_every_domain_error_is_catchable_as_domain_error(exc: DomainError) -> None:
    assert isinstance(exc, DomainError)


@pytest.mark.parametrize("exc", [InvalidEmail("x"), InvalidScore("x"), InvalidReplyDraft("x")])
def test_value_object_errors_share_a_validation_base(exc: DomainError) -> None:
    assert isinstance(exc, ValidationError)


def test_invalid_transition_carries_both_ends_and_names_them() -> None:
    exc = InvalidLeadStatusTransition("qualified", "received")
    assert exc.from_status == "qualified"
    assert exc.to_status == "received"
    assert "qualified" in str(exc) and "received" in str(exc)


def test_invalid_email_keeps_the_offending_input() -> None:
    assert InvalidEmail("bad@@x").raw == "bad@@x"


def test_lead_not_found_carries_the_id() -> None:
    exc = LeadNotFound("abc-123")
    assert exc.lead_id == "abc-123"
    assert "abc-123" in str(exc)
