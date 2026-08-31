"""SQLAlchemy ORM models. Column shapes mirror migration ``0001_baseline``."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_NOW = text("now()")
_TS = DateTime(timezone=True)


class Base(DeclarativeBase):
    pass


class LeadChildRow:
    """Mixin for the tables that hold exactly one row per lead."""

    id: Mapped[UUID] = mapped_column(primary_key=True)
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), unique=True)
    created_at: Mapped[datetime] = mapped_column(_TS, server_default=_NOW)


class LeadRow(Base):
    __tablename__ = "leads"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="received")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(_TS, server_default=_NOW)
    updated_at: Mapped[datetime] = mapped_column(_TS, server_default=_NOW)

    __table_args__ = (
        Index("ix_leads_email_source", "email", "source"),
        Index("ix_leads_status", "status"),
        Index("ix_leads_created_at", text("created_at DESC")),
    )


class EnrichmentRow(LeadChildRow, Base):
    __tablename__ = "enrichments"

    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company_size_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    intent_signals: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))


class ScoreRow(LeadChildRow, Base):
    __tablename__ = "scores"

    value: Mapped[int] = mapped_column(Integer)
    band: Mapped[str] = mapped_column(String(10))
    rationale: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("value >= 0 AND value <= 100", name="ck_scores_value_range"),
        CheckConstraint("band IN ('hot', 'warm', 'cold')", name="ck_scores_band"),
    )


class ReplyDraftRow(LeadChildRow, Base):
    __tablename__ = "reply_drafts"

    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)


class SyncStateRow(LeadChildRow, Base):
    __tablename__ = "sync_state"

    crm_contact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(10), server_default="pending")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(_TS, server_default=_NOW)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'synced', 'failed')", name="ck_sync_state_status"),
    )


class TaskRow(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), server_default="queued")
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    run_after: Mapped[datetime] = mapped_column(_TS, server_default=_NOW)
    locked_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(_TS, server_default=_NOW)
    updated_at: Mapped[datetime] = mapped_column(_TS, server_default=_NOW)

    __table_args__ = (
        CheckConstraint("kind IN ('enrich', 'sync')", name="ck_tasks_kind"),
        CheckConstraint(
            "status IN ('queued', 'in_progress', 'done', 'failed')", name="ck_tasks_status"
        ),
        Index("ix_tasks_claim", "status", "run_after"),
    )
