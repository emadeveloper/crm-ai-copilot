"""PostgreSQL-backed :class:`LeadRepository`."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence import mappers
from app.adapters.persistence.models import (
    EnrichmentRow,
    LeadChildRow,
    LeadRow,
    ReplyDraftRow,
    ScoreRow,
    SyncStateRow,
)
from app.domain.lead import Lead
from app.domain.lead_aggregate import LeadAggregate
from app.domain.ports import LeadAnalysis
from app.domain.sync_state import SyncState
from app.domain.value_objects import Email, LeadId


class SqlLeadRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def save(self, lead: Lead) -> None:
        async with self._sessionmaker() as session, session.begin():
            await session.merge(mappers.lead_to_row(lead))

    async def get(self, lead_id: LeadId) -> Lead | None:
        async with self._sessionmaker() as session:
            row = await session.get(LeadRow, lead_id.value)
            return mappers.row_to_lead(row) if row is not None else None

    async def find_recent_duplicate(
        self, *, email: Email, source: str, since: datetime
    ) -> Lead | None:
        stmt = (
            select(LeadRow)
            .where(
                LeadRow.email == str(email),
                LeadRow.source == source,
                LeadRow.created_at >= since,
            )
            .order_by(LeadRow.created_at.desc())
            .limit(1)
        )
        async with self._sessionmaker() as session:
            row = (await session.execute(stmt)).scalar_one_or_none()
            return mappers.row_to_lead(row) if row is not None else None

    async def save_analysis(self, lead_id: LeadId, analysis: LeadAnalysis) -> None:
        async with self._sessionmaker() as session, session.begin():
            await session.execute(
                delete(EnrichmentRow).where(EnrichmentRow.lead_id == lead_id.value)
            )
            await session.execute(delete(ScoreRow).where(ScoreRow.lead_id == lead_id.value))
            await session.execute(
                delete(ReplyDraftRow).where(ReplyDraftRow.lead_id == lead_id.value)
            )
            session.add(mappers.enrichment_to_row(lead_id, analysis.enrichment))
            session.add(mappers.score_to_row(lead_id, analysis.score))
            session.add(mappers.reply_draft_to_row(lead_id, analysis.reply_draft))

    async def save_sync_state(self, lead_id: LeadId, sync_state: SyncState) -> None:
        async with self._sessionmaker() as session, session.begin():
            await session.execute(delete(SyncStateRow).where(SyncStateRow.lead_id == lead_id.value))
            session.add(mappers.sync_state_to_row(lead_id, sync_state))

    async def get_aggregate(self, lead_id: LeadId) -> LeadAggregate | None:
        async with self._sessionmaker() as session:
            lead_row = await session.get(LeadRow, lead_id.value)
            if lead_row is None:
                return None
            enrichment = await _one(session, EnrichmentRow, lead_id.value)
            score = await _one(session, ScoreRow, lead_id.value)
            reply_draft = await _one(session, ReplyDraftRow, lead_id.value)
            sync_state = await _one(session, SyncStateRow, lead_id.value)
            return LeadAggregate(
                lead=mappers.row_to_lead(lead_row),
                enrichment=mappers.row_to_enrichment(enrichment) if enrichment else None,
                score=mappers.row_to_score(score) if score else None,
                reply_draft=mappers.row_to_reply_draft(reply_draft) if reply_draft else None,
                sync_state=mappers.row_to_sync_state(sync_state) if sync_state else None,
            )

    async def list_aggregates(self, *, limit: int, offset: int) -> list[LeadAggregate]:
        async with self._sessionmaker() as session:
            lead_rows = list(
                (
                    await session.execute(
                        select(LeadRow)
                        .order_by(LeadRow.created_at.desc())
                        .limit(limit)
                        .offset(offset)
                    )
                ).scalars()
            )
            if not lead_rows:
                return []
            ids = [row.id for row in lead_rows]
            enr = await _by_lead(session, EnrichmentRow, ids)
            sco = await _by_lead(session, ScoreRow, ids)
            rep = await _by_lead(session, ReplyDraftRow, ids)
            syn = await _by_lead(session, SyncStateRow, ids)
            return [
                LeadAggregate(
                    lead=mappers.row_to_lead(row),
                    enrichment=mappers.row_to_enrichment(enr[row.id]) if row.id in enr else None,
                    score=mappers.row_to_score(sco[row.id]) if row.id in sco else None,
                    reply_draft=(
                        mappers.row_to_reply_draft(rep[row.id]) if row.id in rep else None
                    ),
                    sync_state=(mappers.row_to_sync_state(syn[row.id]) if row.id in syn else None),
                )
                for row in lead_rows
            ]


async def _one[C: LeadChildRow](session: AsyncSession, model: type[C], lead_id: UUID) -> C | None:
    result = await session.execute(select(model).where(model.lead_id == lead_id))
    return result.scalar_one_or_none()


async def _by_lead[C: LeadChildRow](
    session: AsyncSession, model: type[C], lead_ids: list[UUID]
) -> dict[UUID, C]:
    result = await session.execute(select(model).where(model.lead_id.in_(lead_ids)))
    return {row.lead_id: row for row in result.scalars()}
