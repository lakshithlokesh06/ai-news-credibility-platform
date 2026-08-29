"""add transformer training metadata

Revision ID: 20260829_0003
Revises: 20260828_0002
Create Date: 2026-08-29
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260829_0003"
down_revision: str | None = "20260828_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ml_training_runs",
        sa.Column("model_family", sa.String(length=32), nullable=False, server_default="classical"),
    )
    op.add_column("ml_training_runs", sa.Column("base_model_name", sa.String(length=255), nullable=True))
    op.add_column(
        "ml_training_runs",
        sa.Column("transformer_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column("ml_training_runs", sa.Column("device_used", sa.String(length=64), nullable=True))
    op.add_column("ml_training_runs", sa.Column("training_duration_seconds", sa.Float(), nullable=True))
    op.create_index("ix_ml_training_runs_model_family", "ml_training_runs", ["model_family"], unique=False)
    op.create_index("ix_ml_training_runs_family_status", "ml_training_runs", ["model_family", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ml_training_runs_family_status", table_name="ml_training_runs")
    op.drop_index("ix_ml_training_runs_model_family", table_name="ml_training_runs")
    op.drop_column("ml_training_runs", "training_duration_seconds")
    op.drop_column("ml_training_runs", "device_used")
    op.drop_column("ml_training_runs", "transformer_config")
    op.drop_column("ml_training_runs", "base_model_name")
    op.drop_column("ml_training_runs", "model_family")
