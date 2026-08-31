"""Pydantic request/response models for the REST API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain.lead_aggregate import LeadAggregate


class ContactIn(BaseModel):
    name: str
    email: str
    company: str | None = None
    role: str | None = None
    message: str | None = None


class LeadIn(BaseModel):
    source: str
    contact: ContactIn


class LeadCreatedOut(BaseModel):
    id: str
    deduplicated: bool


class ContactOut(BaseModel):
    name: str
    email: str
    company: str | None
    role: str | None
    message: str | None


class EnrichmentOut(BaseModel):
    industry: str | None
    company_size_band: str | None
    seniority: str | None
    intent_signals: list[str]


class ScoreOut(BaseModel):
    value: int
    band: str
    rationale: str


class ReplyDraftOut(BaseModel):
    subject: str
    body: str


class SyncStateOut(BaseModel):
    status: str
    crm_contact_id: str | None
    failure_reason: str | None
    synced_at: datetime | None


class LeadOut(BaseModel):
    id: str
    source: str
    status: str
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    contact: ContactOut
    enrichment: EnrichmentOut | None
    score: ScoreOut | None
    reply_draft: ReplyDraftOut | None
    sync_state: SyncStateOut | None

    @classmethod
    def from_aggregate(cls, agg: LeadAggregate) -> LeadOut:
        lead = agg.lead
        return cls(
            id=str(lead.id),
            source=lead.source,
            status=str(lead.status),
            failure_reason=lead.failure_reason,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
            contact=ContactOut(
                name=lead.contact.name,
                email=str(lead.contact.email),
                company=lead.contact.company,
                role=lead.contact.role,
                message=lead.contact.message,
            ),
            enrichment=(
                EnrichmentOut(
                    industry=agg.enrichment.industry,
                    company_size_band=agg.enrichment.company_size_band,
                    seniority=agg.enrichment.seniority,
                    intent_signals=list(agg.enrichment.intent_signals),
                )
                if agg.enrichment
                else None
            ),
            score=(
                ScoreOut(
                    value=agg.score.value,
                    band=str(agg.score.band),
                    rationale=agg.score.rationale,
                )
                if agg.score
                else None
            ),
            reply_draft=(
                ReplyDraftOut(subject=agg.reply_draft.subject, body=agg.reply_draft.body)
                if agg.reply_draft
                else None
            ),
            sync_state=(
                SyncStateOut(
                    status=str(agg.sync_state.status),
                    crm_contact_id=(
                        str(agg.sync_state.crm_contact_id)
                        if agg.sync_state.crm_contact_id
                        else None
                    ),
                    failure_reason=agg.sync_state.failure_reason,
                    synced_at=agg.sync_state.synced_at,
                )
                if agg.sync_state
                else None
            ),
        )
