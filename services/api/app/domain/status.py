"""The lead lifecycle and its permitted transitions.

`received -> enriching -> qualified -> syncing -> synced` is the forward path. Any non-terminal
state may drop to `failed`. The only backward moves are explicit retries out of `failed`.
"""

from __future__ import annotations

from enum import StrEnum

from app.domain.errors import InvalidLeadStatusTransition


class LeadStatus(StrEnum):
    RECEIVED = "received"
    ENRICHING = "enriching"
    QUALIFIED = "qualified"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


_ALLOWED: dict[LeadStatus, frozenset[LeadStatus]] = {
    LeadStatus.RECEIVED: frozenset({LeadStatus.ENRICHING, LeadStatus.FAILED}),
    LeadStatus.ENRICHING: frozenset({LeadStatus.QUALIFIED, LeadStatus.FAILED}),
    LeadStatus.QUALIFIED: frozenset({LeadStatus.SYNCING, LeadStatus.FAILED}),
    LeadStatus.SYNCING: frozenset({LeadStatus.SYNCED, LeadStatus.FAILED}),
    LeadStatus.SYNCED: frozenset(),
    LeadStatus.FAILED: frozenset({LeadStatus.ENRICHING, LeadStatus.SYNCING}),
}


def can_transition(current: LeadStatus, target: LeadStatus) -> bool:
    """Return whether moving from ``current`` to ``target`` is permitted."""
    return target in _ALLOWED[current]


def assert_transition(current: LeadStatus, target: LeadStatus) -> None:
    """Raise :class:`InvalidLeadStatusTransition` if the move is not permitted."""
    if not can_transition(current, target):
        raise InvalidLeadStatusTransition(current, target)
