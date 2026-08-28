import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class ArticleLabel(StrEnum):
    REAL = "REAL"
    FAKE = "FAKE"


class ImportStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DatasetImportRun(Base):
    __tablename__ = "dataset_import_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ImportStatus.PENDING.value)
    total_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    successfully_imported_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    skipped_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    invalid_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    articles: Mapped[list["NewsArticle"]] = relationship(back_populates="import_run")

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="ck_dataset_import_runs_status",
        ),
        Index("ix_dataset_import_runs_dataset_started", "dataset_name", "started_at"),
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    label: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duplicate_key: Mapped[str] = mapped_column(String(64), nullable=False)
    import_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("dataset_import_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    import_run: Mapped[DatasetImportRun | None] = relationship(back_populates="articles")

    __table_args__ = (
        CheckConstraint("label IN ('REAL', 'FAKE')", name="ck_news_articles_label"),
        CheckConstraint("title IS NOT NULL OR content IS NOT NULL", name="ck_news_articles_title_or_content"),
        UniqueConstraint("dataset_name", "duplicate_key", name="uq_news_articles_dataset_duplicate_key"),
        Index("ix_news_articles_dataset_label", "dataset_name", "label"),
        Index("ix_news_articles_source_dataset", "source_name", "dataset_name"),
    )

