import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.training import MLTrainingRun


class MonitoringProfileStatus:
    ACTIVE = "active"


class ModelMonitoringProfile(Base):
    __tablename__ = "model_monitoring_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ml_training_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=MonitoringProfileStatus.ACTIVE)
    sample_count: Mapped[int] = mapped_column(nullable=False)
    reference_statistics: Mapped[dict] = mapped_column(JSON, nullable=False)
    reference_label_distribution: Mapped[dict] = mapped_column(JSON, nullable=False)
    feature_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    training_run: Mapped[MLTrainingRun] = relationship()

    __table_args__ = (
        UniqueConstraint("training_run_id", "profile_version", name="uq_monitoring_profile_training_version"),
        Index("ix_monitoring_profiles_training_status", "training_run_id", "status"),
    )
