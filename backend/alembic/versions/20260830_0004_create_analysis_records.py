"""create analysis records

Revision ID: 20260830_0004
Revises: 20260829_0003
Create Date: 2026-08-30
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260830_0004"
down_revision: str | None = "20260829_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_run_id", sa.Uuid(), nullable=True),
        sa.Column("model_family", sa.String(length=32), nullable=False),
        sa.Column("model_type", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("model_display_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=1000), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("text_composition_mode", sa.String(length=64), nullable=True),
        sa.Column("predicted_label", sa.String(length=16), nullable=False),
        sa.Column("real_probability", sa.Float(), nullable=True),
        sa.Column("fake_probability", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("probability_method", sa.String(length=128), nullable=True),
        sa.Column("explanation_status", sa.String(length=32), nullable=False),
        sa.Column("explanation_method", sa.String(length=128), nullable=True),
        sa.Column("explained_class", sa.String(length=16), nullable=True),
        sa.Column(
            "influences_toward_real",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "influences_toward_fake",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "explanation_limitations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("explanation_message", sa.Text(), nullable=True),
        sa.Column("explanation_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("predicted_label IN ('REAL', 'FAKE')", name="ck_analysis_records_predicted_label"),
        sa.CheckConstraint(
            "explanation_status IN ('not_requested', 'generated', 'failed')",
            name="ck_analysis_records_explanation_status",
        ),
        sa.ForeignKeyConstraint(["training_run_id"], ["ml_training_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_records_created_at", "analysis_records", ["created_at"], unique=False)
    op.create_index("ix_analysis_records_created_label", "analysis_records", ["created_at", "predicted_label"], unique=False)
    op.create_index("ix_analysis_records_explanation_status", "analysis_records", ["explanation_status"], unique=False)
    op.create_index("ix_analysis_records_family_type", "analysis_records", ["model_family", "model_type"], unique=False)
    op.create_index("ix_analysis_records_model_family", "analysis_records", ["model_family"], unique=False)
    op.create_index("ix_analysis_records_model_type", "analysis_records", ["model_type"], unique=False)
    op.create_index("ix_analysis_records_predicted_label", "analysis_records", ["predicted_label"], unique=False)
    op.create_index("ix_analysis_records_training_run_id", "analysis_records", ["training_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_analysis_records_training_run_id", table_name="analysis_records")
    op.drop_index("ix_analysis_records_predicted_label", table_name="analysis_records")
    op.drop_index("ix_analysis_records_model_type", table_name="analysis_records")
    op.drop_index("ix_analysis_records_model_family", table_name="analysis_records")
    op.drop_index("ix_analysis_records_family_type", table_name="analysis_records")
    op.drop_index("ix_analysis_records_explanation_status", table_name="analysis_records")
    op.drop_index("ix_analysis_records_created_label", table_name="analysis_records")
    op.drop_index("ix_analysis_records_created_at", table_name="analysis_records")
    op.drop_table("analysis_records")
