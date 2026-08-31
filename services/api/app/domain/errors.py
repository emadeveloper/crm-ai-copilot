"""Domain error hierarchy. No dependencies on other domain modules (avoids import cycles)."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every expected domain-level failure."""


class InvalidLeadStatusTransition(DomainError):
    """Raised when a lead status change is not permitted by the lifecycle."""

    def __init__(self, from_status: str, to_status: str) -> None:
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"cannot transition lead from {from_status} to {to_status}")


class ValidationError(DomainError):
    """Base class for value-object / entity invariant violations."""


class InvalidEmail(ValidationError):
    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"not a valid email address: {raw!r}")


class InvalidScore(ValidationError):
    """Raised when a score value, band, or rationale breaks an invariant."""


class InvalidReplyDraft(ValidationError):
    """Raised when a reply draft is missing its subject or body."""


class LeadNotFound(DomainError):
    """Raised when a lookup by id finds no lead."""

    def __init__(self, lead_id: str) -> None:
        self.lead_id = lead_id
        super().__init__(f"no lead with id {lead_id}")
