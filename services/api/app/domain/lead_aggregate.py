"""A lead together with whatever derived data has been produced so far.

This is the read model the API returns for a single lead and for the queue list.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enrichment import Enrichment
from app.domain.lead import Lead
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score
from app.domain.sync_state import SyncState


@dataclass(frozen=True, slots=True)
class LeadAggregate:
    lead: Lead
    enrichment: Enrichment | None = None
    score: Score | None = None
    reply_draft: ReplyDraft | None = None
    sync_state: SyncState | None = None
