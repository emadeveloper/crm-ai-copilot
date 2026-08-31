"""Push a qualified lead — its score and reply draft — into the CRM."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.application.errors import CrmError, LeadNotReadyForSync
from app.domain.errors import LeadNotFound
from app.domain.ports import CrmGateway, LeadRepository
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score
from app.domain.status import LeadStatus
from app.domain.sync_state import SyncState
from app.domain.value_objects import LeadId

_ADVANCEABLE_TO_SYNCING = (LeadStatus.QUALIFIED, LeadStatus.FAILED)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def render_note(score: Score, reply_draft: ReplyDraft) -> str:
    """Human-readable CRM note carrying the score and the drafted reply."""
    return (
        f"AI lead score: {score.value}/100 ({score.band}).\n"
        f"Rationale: {score.rationale}\n\n"
        f"Suggested first reply\n"
        f"Subject: {reply_draft.subject}\n"
        f"{reply_draft.body}"
    )


class SyncLeadToCrm:
    def __init__(
        self,
        *,
        leads: LeadRepository,
        crm: CrmGateway,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._leads = leads
        self._crm = crm
        self._clock = clock

    async def execute(self, lead_id: LeadId) -> None:
        aggregate = await self._leads.get_aggregate(lead_id)
        if aggregate is None:
            raise LeadNotFound(str(lead_id))
        if aggregate.score is None or aggregate.reply_draft is None:
            raise LeadNotReadyForSync(str(lead_id))

        lead = aggregate.lead
        sync_state = aggregate.sync_state or SyncState.pending()

        if lead.status in _ADVANCEABLE_TO_SYNCING:
            lead.advance_to(LeadStatus.SYNCING, now=self._clock())
            await self._leads.save(lead)

        note = render_note(aggregate.score, aggregate.reply_draft)
        try:
            contact_id = sync_state.crm_contact_id or await self._crm.upsert_contact(lead)
            sync_state.crm_contact_id = contact_id
            await self._crm.attach_note(contact_id, note)
        except CrmError as exc:
            # Record the failure (keeping any discovered contact id), then let it propagate so
            # the caller / worker can reschedule the sync task. Derived data is untouched.
            sync_state.mark_failed(str(exc))
            await self._leads.save_sync_state(lead_id, sync_state)
            raise

        sync_state.mark_synced(contact_id, at=self._clock())
        await self._leads.save_sync_state(lead_id, sync_state)

        if lead.status is LeadStatus.SYNCING:
            lead.advance_to(LeadStatus.SYNCED, now=self._clock())
            await self._leads.save(lead)
