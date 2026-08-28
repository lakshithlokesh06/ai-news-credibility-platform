"""create ml training runs table

Revision ID: 20260828_0002
Revises: 20260828_0001
Create Date: 2026-08-28
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260828_0002"
down_revision: str | None = "20260828_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ml_training_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_type", sa.String(length=64), nullable=False),
        sa.Column("model_display_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("preprocessing_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("text_composition_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tfidf_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_hyperparameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("split_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("random_seed", sa.Integer(), nullable=False),
        sa.Column("train_count", sa.Integer(), nullable=False),
        sa.Column("validation_count", sa.Integer(), nullable=False),
        sa.Column("test_count", sa.Integer(), nullable=False),
        sa.Column("dataset_article_count", sa.Integer(), nullable=False),
        sa.Column("dataset_identifiers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("split_distributions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("test_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("artifact_path", sa.String(length=512), nullable=True),
        sa.Column("artifact_checksum", sa.String(length=64), nullable=True),
        sa.Column("artifact_version", sa.String(length=32), nullable=True),
        sa.Column("probability_method", sa.String(length=128), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_training_runs_model_type", "ml_training_runs", ["model_type"], unique=False)
    op.create_index("ix_ml_training_runs_status", "ml_training_runs", ["status"], unique=False)
    op.create_index("ix_ml_training_runs_status_started", "ml_training_runs", ["status", "started_at"], unique=False)
    op.create_index("ix_ml_training_runs_model_status", "ml_training_runs", ["model_type", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ml_training_runs_model_status", table_name="ml_training_runs")
    op.drop_index("ix_ml_training_runs_status_started", table_name="ml_training_runs")
    op.drop_index("ix_ml_training_runs_status", table_name="ml_training_runs")
    op.drop_index("ix_ml_training_runs_model_type", table_name="ml_training_runs")
    op.drop_table("ml_training_runs")

