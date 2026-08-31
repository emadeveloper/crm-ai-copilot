"""baseline schema: leads, enrichments, scores, reply_drafts, sync_state, tasks

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = sa.text("now()")
_UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", _UUID, primary_key=True),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("role", sa.String(200), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
    )
    op.create_index("ix_leads_email_source", "leads", ["email", "source"])
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index("ix_leads_created_at", "leads", [sa.text("created_at DESC")])

    _one_to_one_child(
        "enrichments",
        sa.Column("industry", sa.String(200), nullable=True),
        sa.Column("company_size_band", sa.String(50), nullable=True),
        sa.Column("seniority", sa.String(50), nullable=True),
        sa.Column(
            "intent_signals",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    _one_to_one_child(
        "scores",
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("band", sa.String(10), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.CheckConstraint("value >= 0 AND value <= 100", name="ck_scores_value_range"),
        sa.CheckConstraint("band IN ('hot', 'warm', 'cold')", name="ck_scores_band"),
    )

    _one_to_one_child(
        "reply_drafts",
        sa.Column("subject", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
    )

    op.create_table(
        "sync_state",
        sa.Column("id", _UUID, primary_key=True),
        sa.Column(
            "lead_id",
            _UUID,
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("crm_contact_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
        sa.CheckConstraint(
            "status IN ('pending', 'synced', 'failed')", name="ck_sync_state_status"
        ),
    )

    op.create_table(
        "tasks",
        sa.Column("id", _UUID, primary_key=True),
        sa.Column(
            "lead_id",
            _UUID,
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("run_after", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(120), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
        sa.CheckConstraint("kind IN ('enrich', 'sync')", name="ck_tasks_kind"),
        sa.CheckConstraint(
            "status IN ('queued', 'in_progress', 'done', 'failed')", name="ck_tasks_status"
        ),
    )
    # Supports the claim query: WHERE status = 'queued' AND run_after <= now() ORDER BY run_after
    op.create_index("ix_tasks_claim", "tasks", ["status", "run_after"])


def _one_to_one_child(table: str, *columns: sa.Column | sa.SchemaItem) -> None:
    """Create a table that holds exactly one row per lead (nullable until produced)."""
    op.create_table(
        table,
        sa.Column("id", _UUID, primary_key=True),
        sa.Column(
            "lead_id",
            _UUID,
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        *columns,
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_NOW),
    )


def downgrade() -> None:
    for table in ("tasks", "sync_state", "reply_drafts", "scores", "enrichments", "leads"):
        op.drop_table(table)
