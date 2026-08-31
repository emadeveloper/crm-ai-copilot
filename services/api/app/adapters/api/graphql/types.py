"""Strawberry GraphQL types. Same shape and values as the REST ``LeadOut``."""

from __future__ import annotations

from datetime import datetime

import strawberry

from app.domain.lead_aggregate import LeadAggregate


@strawberry.type
class Contact:
    name: str
    email: str
    company: str | None
    role: str | None
    message: str | None


@strawberry.type
class Enrichment:
    industry: str | None
    company_size_band: str | None
    seniority: str | None
    intent_signals: list[str]


@strawberry.type
class Score:
    value: int
    band: str
    rationale: str


@strawberry.type
class ReplyDraft:
    subject: str
    body: str


@strawberry.type
class SyncState:
    status: str
    crm_contact_id: str | None
    failure_reason: str | None
    synced_at: datetime | None


@strawberry.type
class Lead:
    id: str
    source: str
    status: str
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    contact: Contact
    enrichment: Enrichment | None
    score: Score | None
    reply_draft: ReplyDraft | None
    sync_state: SyncState | None


def lead_from_aggregate(agg: LeadAggregate) -> Lead:
    lead = agg.lead
    return Lead(
        id=str(lead.id),
        source=lead.source,
        status=str(lead.status),
        failure_reason=lead.failure_reason,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        contact=Contact(
            name=lead.contact.name,
            email=str(lead.contact.email),
            company=lead.contact.company,
            role=lead.contact.role,
            message=lead.contact.message,
        ),
        enrichment=(
            Enrichment(
                industry=agg.enrichment.industry,
                company_size_band=agg.enrichment.company_size_band,
                seniority=agg.enrichment.seniority,
                intent_signals=list(agg.enrichment.intent_signals),
            )
            if agg.enrichment
            else None
        ),
        score=(
            Score(value=agg.score.value, band=str(agg.score.band), rationale=agg.score.rationale)
            if agg.score
            else None
        ),
        reply_draft=(
            ReplyDraft(subject=agg.reply_draft.subject, body=agg.reply_draft.body)
            if agg.reply_draft
            else None
        ),
        sync_state=(
            SyncState(
                status=str(agg.sync_state.status),
                crm_contact_id=(
                    str(agg.sync_state.crm_contact_id) if agg.sync_state.crm_contact_id else None
                ),
                failure_reason=agg.sync_state.failure_reason,
                synced_at=agg.sync_state.synced_at,
            )
            if agg.sync_state
            else None
        ),
    )
