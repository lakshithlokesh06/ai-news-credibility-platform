import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.training import MLTrainingRun


class ExplanationStatus:
    NOT_REQUESTED = "not_requested"
    GENERATED = "generated"
    FAILED = "failed"


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ml_training_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_family: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_composition_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    predicted_label: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    real_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    fake_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    probability_method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    explanation_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ExplanationStatus.NOT_REQUESTED,
        index=True,
    )
    explanation_method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    explained_class: Mapped[str | None] = mapped_column(String(16), nullable=True)
    influences_toward_real: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    influences_toward_fake: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explanation_limitations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explanation_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    training_run: Mapped[MLTrainingRun | None] = relationship()
    review: Mapped["AnalysisReview | None"] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        uselist=False,
    )
    claims: Mapped[list["AnalysisClaim"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="AnalysisClaim.created_at.desc()",
    )

    __table_args__ = (
        CheckConstraint("predicted_label IN ('REAL', 'FAKE')", name="ck_analysis_records_predicted_label"),
        CheckConstraint(
            "explanation_status IN ('not_requested', 'generated', 'failed')",
            name="ck_analysis_records_explanation_status",
        ),
        Index("ix_analysis_records_created_label", "created_at", "predicted_label"),
        Index("ix_analysis_records_family_type", "model_family", "model_type"),
    )
