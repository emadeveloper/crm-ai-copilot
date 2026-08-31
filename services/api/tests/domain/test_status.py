"""Task 2.1 — LeadStatus lifecycle guard (spec: lead-pipeline / Status lifecycle)."""

from __future__ import annotations

import pytest

from app.domain.errors import InvalidLeadStatusTransition
from app.domain.status import LeadStatus, assert_transition, can_transition

HAPPY_PATH = [
    (LeadStatus.RECEIVED, LeadStatus.ENRICHING),
    (LeadStatus.ENRICHING, LeadStatus.QUALIFIED),
    (LeadStatus.QUALIFIED, LeadStatus.SYNCING),
    (LeadStatus.SYNCING, LeadStatus.SYNCED),
]


@pytest.mark.parametrize(("current", "target"), HAPPY_PATH)
def test_forward_progression_is_allowed(current: LeadStatus, target: LeadStatus) -> None:
    assert can_transition(current, target) is True


@pytest.mark.parametrize("current", list(LeadStatus))
def test_any_non_terminal_state_can_fail(current: LeadStatus) -> None:
    expected = current not in (LeadStatus.SYNCED, LeadStatus.FAILED)
    assert can_transition(current, LeadStatus.FAILED) is expected


def test_synced_is_terminal() -> None:
    for target in LeadStatus:
        assert can_transition(LeadStatus.SYNCED, target) is False


def test_cannot_skip_steps() -> None:
    assert can_transition(LeadStatus.RECEIVED, LeadStatus.SYNCED) is False
    assert can_transition(LeadStatus.RECEIVED, LeadStatus.QUALIFIED) is False
    assert can_transition(LeadStatus.ENRICHING, LeadStatus.SYNCING) is False


def test_only_retry_transitions_go_backward_from_failed() -> None:
    assert can_transition(LeadStatus.FAILED, LeadStatus.ENRICHING) is True
    assert can_transition(LeadStatus.FAILED, LeadStatus.SYNCING) is True
    assert can_transition(LeadStatus.FAILED, LeadStatus.QUALIFIED) is False
    assert can_transition(LeadStatus.FAILED, LeadStatus.SYNCED) is False


def test_assert_transition_passes_silently_when_allowed() -> None:
    assert_transition(LeadStatus.RECEIVED, LeadStatus.ENRICHING)  # must not raise


def test_assert_transition_raises_with_context_when_forbidden() -> None:
    with pytest.raises(InvalidLeadStatusTransition) as exc_info:
        assert_transition(LeadStatus.SYNCED, LeadStatus.ENRICHING)

    err = exc_info.value
    assert err.from_status == LeadStatus.SYNCED
    assert err.to_status == LeadStatus.ENRICHING
    assert "synced" in str(err) and "enriching" in str(err)
