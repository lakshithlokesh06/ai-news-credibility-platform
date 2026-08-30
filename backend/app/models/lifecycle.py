import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.training import MLTrainingRun


class ModelLifecycleEventType(StrEnum):
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"
    RESTORED = "restored"


class ModelLifecycleEvent(Base):
    __tablename__ = "model_lifecycle_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ml_training_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_champion_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ml_training_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    training_run: Mapped[MLTrainingRun] = relationship(foreign_keys=[training_run_id])
    previous_champion: Mapped[MLTrainingRun | None] = relationship(foreign_keys=[previous_champion_id])

    __table_args__ = (
        Index("ix_lifecycle_events_run_created", "training_run_id", "created_at"),
    )
