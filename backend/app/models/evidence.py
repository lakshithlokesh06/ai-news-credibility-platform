import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class ClaimStatus(StrEnum):
    OPEN = "open"
    REVIEWED = "reviewed"


class EvidenceAssessment(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"
    UNCLEAR = "unclear"


class AnalysisClaim(Base):
    __tablename__ = "analysis_claims"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ClaimStatus.OPEN.value, index=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    analysis: Mapped["AnalysisRecord"] = relationship(back_populates="claims")
    evidence_items: Mapped[list["ClaimEvidence"]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
        order_by="ClaimEvidence.created_at.desc()",
    )

    __table_args__ = (
        CheckConstraint("status IN ('open', 'reviewed')", name="ck_analysis_claims_status"),
        CheckConstraint(
            "(start_offset IS NULL AND end_offset IS NULL) OR (start_offset >= 0 AND end_offset > start_offset)",
            name="ck_analysis_claims_offsets",
        ),
        Index("ix_analysis_claims_analysis_status", "analysis_id", "status"),
        Index("ix_analysis_claims_updated_at", "updated_at"),
    )


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assessment: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    evidence_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    claim: Mapped[AnalysisClaim] = relationship(back_populates="evidence_items")

    __table_args__ = (
        CheckConstraint(
            "assessment IN ('supports', 'contradicts', 'neutral', 'unclear')",
            name="ck_claim_evidence_assessment",
        ),
        UniqueConstraint("claim_id", "normalized_source_url", name="uq_claim_evidence_claim_normalized_url"),
        Index("ix_claim_evidence_claim_assessment", "claim_id", "assessment"),
        Index("ix_claim_evidence_updated_at", "updated_at"),
    )
