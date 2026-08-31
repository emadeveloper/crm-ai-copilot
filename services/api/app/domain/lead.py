"""The Lead entity — the aggregate root of the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.contact_details import ContactDetails
from app.domain.status import LeadStatus, assert_transition
from app.domain.value_objects import LeadId


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class Lead:
    id: LeadId
    source: str
    contact: ContactDetails
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    failure_reason: str | None = None

    @classmethod
    def register(cls, *, source: str, contact: ContactDetails, now: datetime | None = None) -> Lead:
        timestamp = now or _utcnow()
        return cls(
            id=LeadId.new(),
            source=source.strip(),
            contact=contact,
            status=LeadStatus.RECEIVED,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def advance_to(self, target: LeadStatus, *, now: datetime | None = None) -> None:
        assert_transition(self.status, target)
        self.status = target
        self.updated_at = now or _utcnow()

    def mark_failed(self, reason: str, *, now: datetime | None = None) -> None:
        self.advance_to(LeadStatus.FAILED, now=now)
        self.failure_reason = reason
