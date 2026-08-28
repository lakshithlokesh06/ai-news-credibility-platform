"""create news article and import tracking tables

Revision ID: 20260828_0001
Revises:
Create Date: 2026-08-28
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260828_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dataset_import_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_name", sa.String(length=255), nullable=False),
        sa.Column("source_filename", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("successfully_imported_rows", sa.Integer(), nullable=False),
        sa.Column("skipped_rows", sa.Integer(), nullable=False),
        sa.Column("invalid_rows", sa.Integer(), nullable=False),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="ck_dataset_import_runs_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dataset_import_runs_dataset_name",
        "dataset_import_runs",
        ["dataset_name"],
        unique=False,
    )
    op.create_index(
        "ix_dataset_import_runs_dataset_started",
        "dataset_import_runs",
        ["dataset_name", "started_at"],
        unique=False,
    )

    op.create_table(
        "news_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=1000), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("label", sa.String(length=16), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("dataset_name", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("duplicate_key", sa.String(length=64), nullable=False),
        sa.Column("import_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("label IN ('REAL', 'FAKE')", name="ck_news_articles_label"),
        sa.CheckConstraint("title IS NOT NULL OR content IS NOT NULL", name="ck_news_articles_title_or_content"),
        sa.ForeignKeyConstraint(["import_run_id"], ["dataset_import_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_name", "duplicate_key", name="uq_news_articles_dataset_duplicate_key"),
    )
    op.create_index("ix_news_articles_label", "news_articles", ["label"], unique=False)
    op.create_index("ix_news_articles_source_name", "news_articles", ["source_name"], unique=False)
    op.create_index("ix_news_articles_publication_date", "news_articles", ["publication_date"], unique=False)
    op.create_index("ix_news_articles_dataset_name", "news_articles", ["dataset_name"], unique=False)
    op.create_index("ix_news_articles_dataset_label", "news_articles", ["dataset_name", "label"], unique=False)
    op.create_index("ix_news_articles_source_dataset", "news_articles", ["source_name", "dataset_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_news_articles_source_dataset", table_name="news_articles")
    op.drop_index("ix_news_articles_dataset_label", table_name="news_articles")
    op.drop_index("ix_news_articles_dataset_name", table_name="news_articles")
    op.drop_index("ix_news_articles_publication_date", table_name="news_articles")
    op.drop_index("ix_news_articles_source_name", table_name="news_articles")
    op.drop_index("ix_news_articles_label", table_name="news_articles")
    op.drop_table("news_articles")

    op.drop_index("ix_dataset_import_runs_dataset_started", table_name="dataset_import_runs")
    op.drop_index("ix_dataset_import_runs_dataset_name", table_name="dataset_import_runs")
    op.drop_table("dataset_import_runs")

