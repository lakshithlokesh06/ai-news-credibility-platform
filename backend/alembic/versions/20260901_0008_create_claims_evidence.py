"""create claims evidence

Revision ID: 20260901_0008
Revises: 20260831_0007
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260901_0008"
down_revision: str | None = "20260831_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('open', 'reviewed')", name="ck_analysis_claims_status"),
        sa.CheckConstraint(
            "(start_offset IS NULL AND end_offset IS NULL) OR (start_offset >= 0 AND end_offset > start_offset)",
            name="ck_analysis_claims_offsets",
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_claims_analysis_id", "analysis_claims", ["analysis_id"], unique=False)
    op.create_index("ix_analysis_claims_analysis_status", "analysis_claims", ["analysis_id", "status"], unique=False)
    op.create_index("ix_analysis_claims_status", "analysis_claims", ["status"], unique=False)
    op.create_index("ix_analysis_claims_updated_at", "analysis_claims", ["updated_at"], unique=False)

    op.create_table(
        "claim_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("normalized_source_url", sa.String(length=2048), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessment", sa.String(length=32), nullable=False),
        sa.Column("evidence_excerpt", sa.Text(), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "assessment IN ('supports', 'contradicts', 'neutral', 'unclear')",
            name="ck_claim_evidence_assessment",
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["analysis_claims.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_id", "normalized_source_url", name="uq_claim_evidence_claim_normalized_url"),
    )
    op.create_index("ix_claim_evidence_assessment", "claim_evidence", ["assessment"], unique=False)
    op.create_index("ix_claim_evidence_claim_assessment", "claim_evidence", ["claim_id", "assessment"], unique=False)
    op.create_index("ix_claim_evidence_claim_id", "claim_evidence", ["claim_id"], unique=False)
    op.create_index("ix_claim_evidence_updated_at", "claim_evidence", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_claim_evidence_updated_at", table_name="claim_evidence")
    op.drop_index("ix_claim_evidence_claim_id", table_name="claim_evidence")
    op.drop_index("ix_claim_evidence_claim_assessment", table_name="claim_evidence")
    op.drop_index("ix_claim_evidence_assessment", table_name="claim_evidence")
    op.drop_table("claim_evidence")
    op.drop_index("ix_analysis_claims_updated_at", table_name="analysis_claims")
    op.drop_index("ix_analysis_claims_status", table_name="analysis_claims")
    op.drop_index("ix_analysis_claims_analysis_status", table_name="analysis_claims")
    op.drop_index("ix_analysis_claims_analysis_id", table_name="analysis_claims")
    op.drop_table("analysis_claims")
