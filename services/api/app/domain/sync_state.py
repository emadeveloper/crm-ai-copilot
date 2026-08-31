"""Tracks the outcome of syncing a lead to the CRM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.domain.value_objects import CrmContactId


class SyncStatus(StrEnum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass
class SyncState:
    status: SyncStatus
    crm_contact_id: CrmContactId | None = None
    failure_reason: str | None = None
    synced_at: datetime | None = None

    @classmethod
    def pending(cls) -> SyncState:
        return cls(status=SyncStatus.PENDING)

    def mark_synced(self, contact_id: CrmContactId, *, at: datetime | None = None) -> None:
        self.status = SyncStatus.SYNCED
        self.crm_contact_id = contact_id
        self.synced_at = at or datetime.now(UTC)
        self.failure_reason = None

    def mark_failed(self, reason: str) -> None:
        # Keep any contact id already discovered — derived data must not be lost.
        self.status = SyncStatus.FAILED
        self.failure_reason = reason
