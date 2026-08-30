"""add experiment lifecycle

Revision ID: 20260830_0006
Revises: 20260830_0005
Create Date: 2026-08-30
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260830_0006"
down_revision: str | None = "20260830_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ml_training_runs", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "ml_training_runs",
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    )
    op.add_column("ml_training_runs", sa.Column("lifecycle_status", sa.String(length=32), nullable=True))
    op.add_column(
        "ml_training_runs",
        sa.Column("environment_versions", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.add_column("ml_training_runs", sa.Column("champion_promoted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_ml_training_runs_lifecycle_status",
        "ml_training_runs",
        "lifecycle_status IS NULL OR lifecycle_status IN ('candidate', 'champion', 'archived')",
    )
    op.execute("UPDATE ml_training_runs SET lifecycle_status = 'candidate' WHERE status = 'completed' AND lifecycle_status IS NULL")
    op.create_index("ix_ml_training_runs_lifecycle_status", "ml_training_runs", ["lifecycle_status"], unique=False)
    op.create_index(
        "uq_ml_training_runs_one_champion",
        "ml_training_runs",
        ["lifecycle_status"],
        unique=True,
        postgresql_where=sa.text("lifecycle_status = 'champion'"),
    )

    op.create_table(
        "model_lifecycle_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_run_id", sa.Uuid(), nullable=False),
        sa.Column("previous_champion_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["previous_champion_id"], ["ml_training_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["training_run_id"], ["ml_training_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_lifecycle_events_created_at", "model_lifecycle_events", ["created_at"], unique=False)
    op.create_index("ix_model_lifecycle_events_event_type", "model_lifecycle_events", ["event_type"], unique=False)
    op.create_index("ix_model_lifecycle_events_training_run_id", "model_lifecycle_events", ["training_run_id"], unique=False)
    op.create_index("ix_lifecycle_events_run_created", "model_lifecycle_events", ["training_run_id", "created_at"], unique=False)

    op.alter_column("ml_training_runs", "tags", server_default=None)
    op.alter_column("ml_training_runs", "environment_versions", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_lifecycle_events_run_created", table_name="model_lifecycle_events")
    op.drop_index("ix_model_lifecycle_events_training_run_id", table_name="model_lifecycle_events")
    op.drop_index("ix_model_lifecycle_events_event_type", table_name="model_lifecycle_events")
    op.drop_index("ix_model_lifecycle_events_created_at", table_name="model_lifecycle_events")
    op.drop_table("model_lifecycle_events")
    op.drop_index("uq_ml_training_runs_one_champion", table_name="ml_training_runs")
    op.drop_index("ix_ml_training_runs_lifecycle_status", table_name="ml_training_runs")
    op.drop_constraint("ck_ml_training_runs_lifecycle_status", "ml_training_runs", type_="check")
    op.drop_column("ml_training_runs", "champion_promoted_at")
    op.drop_column("ml_training_runs", "environment_versions")
    op.drop_column("ml_training_runs", "lifecycle_status")
    op.drop_column("ml_training_runs", "tags")
    op.drop_column("ml_training_runs", "description")
