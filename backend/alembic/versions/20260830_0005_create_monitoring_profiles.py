"""create monitoring profiles

Revision ID: 20260830_0005
Revises: 20260830_0004
Create Date: 2026-08-30
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260830_0005"
down_revision: str | None = "20260830_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_monitoring_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_run_id", sa.Uuid(), nullable=False),
        sa.Column("profile_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("reference_statistics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reference_label_distribution", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("feature_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["training_run_id"], ["ml_training_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("training_run_id", "profile_version", name="uq_monitoring_profile_training_version"),
    )
    op.create_index("ix_model_monitoring_profiles_training_run_id", "model_monitoring_profiles", ["training_run_id"], unique=False)
    op.create_index("ix_monitoring_profiles_training_status", "model_monitoring_profiles", ["training_run_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_monitoring_profiles_training_status", table_name="model_monitoring_profiles")
    op.drop_index("ix_model_monitoring_profiles_training_run_id", table_name="model_monitoring_profiles")
    op.drop_table("model_monitoring_profiles")
