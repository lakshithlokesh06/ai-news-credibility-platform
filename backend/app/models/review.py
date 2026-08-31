import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class ReviewStatus(StrEnum):
    REVIEWED = "reviewed"


class AnalysisReview(Base):
    __tablename__ = "analysis_reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verified_label: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ReviewStatus.REVIEWED.value, index=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    analysis: Mapped["AnalysisRecord"] = relationship(back_populates="review")

    __table_args__ = (
        CheckConstraint("verified_label IN ('REAL', 'FAKE')", name="ck_analysis_reviews_verified_label"),
        CheckConstraint("status IN ('reviewed')", name="ck_analysis_reviews_status"),
        UniqueConstraint("analysis_id", name="uq_analysis_reviews_analysis_id"),
        Index("ix_analysis_reviews_label_status", "verified_label", "status"),
        Index("ix_analysis_reviews_updated_at", "updated_at"),
    )
