"""Translate between domain objects and ORM rows. Pure functions, no session."""

from __future__ import annotations

from uuid import uuid4

from app.adapters.persistence.models import (
    EnrichmentRow,
    LeadRow,
    ReplyDraftRow,
    ScoreRow,
    SyncStateRow,
)
from app.domain.contact_details import ContactDetails
from app.domain.enrichment import Enrichment
from app.domain.lead import Lead
from app.domain.reply_draft import ReplyDraft
from app.domain.score import Score, ScoreBand
from app.domain.status import LeadStatus
from app.domain.sync_state import SyncState, SyncStatus
from app.domain.value_objects import CrmContactId, Email, LeadId


def lead_to_row(lead: Lead) -> LeadRow:
    return LeadRow(
        id=lead.id.value,
        source=lead.source,
        name=lead.contact.name,
        email=str(lead.contact.email),
        company=lead.contact.company,
        role=lead.contact.role,
        message=lead.contact.message,
        status=str(lead.status),
        failure_reason=lead.failure_reason,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


def row_to_lead(row: LeadRow) -> Lead:
    return Lead(
        id=LeadId(row.id),
        source=row.source,
        contact=ContactDetails(
            name=row.name,
            email=Email(row.email),
            company=row.company,
            role=row.role,
            message=row.message,
        ),
        status=LeadStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
        failure_reason=row.failure_reason,
    )


def enrichment_to_row(lead_id: LeadId, enrichment: Enrichment) -> EnrichmentRow:
    return EnrichmentRow(
        id=uuid4(),
        lead_id=lead_id.value,
        industry=enrichment.industry,
        company_size_band=enrichment.company_size_band,
        seniority=enrichment.seniority,
        intent_signals=list(enrichment.intent_signals),
    )


def row_to_enrichment(row: EnrichmentRow) -> Enrichment:
    return Enrichment(
        industry=row.industry,
        company_size_band=row.company_size_band,
        seniority=row.seniority,
        intent_signals=tuple(row.intent_signals),
    )


def score_to_row(lead_id: LeadId, score: Score) -> ScoreRow:
    return ScoreRow(
        id=uuid4(),
        lead_id=lead_id.value,
        value=score.value,
        band=str(score.band),
        rationale=score.rationale,
    )


def row_to_score(row: ScoreRow) -> Score:
    return Score(value=row.value, band=ScoreBand(row.band), rationale=row.rationale)


def reply_draft_to_row(lead_id: LeadId, draft: ReplyDraft) -> ReplyDraftRow:
    return ReplyDraftRow(id=uuid4(), lead_id=lead_id.value, subject=draft.subject, body=draft.body)


def row_to_reply_draft(row: ReplyDraftRow) -> ReplyDraft:
    return ReplyDraft(subject=row.subject, body=row.body)


def sync_state_to_row(lead_id: LeadId, state: SyncState) -> SyncStateRow:
    return SyncStateRow(
        id=uuid4(),
        lead_id=lead_id.value,
        crm_contact_id=str(state.crm_contact_id) if state.crm_contact_id else None,
        status=str(state.status),
        failure_reason=state.failure_reason,
        synced_at=state.synced_at,
    )


def row_to_sync_state(row: SyncStateRow) -> SyncState:
    return SyncState(
        status=SyncStatus(row.status),
        crm_contact_id=CrmContactId(row.crm_contact_id) if row.crm_contact_id else None,
        failure_reason=row.failure_reason,
        synced_at=row.synced_at,
    )
