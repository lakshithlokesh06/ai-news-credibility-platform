"""create analysis reviews

Revision ID: 20260831_0007
Revises: 20260830_0006
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260831_0007"
down_revision: str | None = "20260830_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("verified_label", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("verified_label IN ('REAL', 'FAKE')", name="ck_analysis_reviews_verified_label"),
        sa.CheckConstraint("status IN ('reviewed')", name="ck_analysis_reviews_status"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id", name="uq_analysis_reviews_analysis_id"),
    )
    op.create_index("ix_analysis_reviews_analysis_id", "analysis_reviews", ["analysis_id"], unique=False)
    op.create_index("ix_analysis_reviews_label_status", "analysis_reviews", ["verified_label", "status"], unique=False)
    op.create_index("ix_analysis_reviews_status", "analysis_reviews", ["status"], unique=False)
    op.create_index("ix_analysis_reviews_updated_at", "analysis_reviews", ["updated_at"], unique=False)
    op.create_index("ix_analysis_reviews_verified_label", "analysis_reviews", ["verified_label"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_analysis_reviews_verified_label", table_name="analysis_reviews")
    op.drop_index("ix_analysis_reviews_updated_at", table_name="analysis_reviews")
    op.drop_index("ix_analysis_reviews_status", table_name="analysis_reviews")
    op.drop_index("ix_analysis_reviews_label_status", table_name="analysis_reviews")
    op.drop_index("ix_analysis_reviews_analysis_id", table_name="analysis_reviews")
    op.drop_table("analysis_reviews")
