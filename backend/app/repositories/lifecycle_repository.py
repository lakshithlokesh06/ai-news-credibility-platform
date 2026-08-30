from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lifecycle import ModelLifecycleEvent


class ModelLifecycleEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, event: ModelLifecycleEvent) -> ModelLifecycleEvent:
        self.db.add(event)
        return event

    def list_for_run(self, training_run_id: UUID, *, limit: int = 25) -> list[ModelLifecycleEvent]:
        return list(
            self.db.execute(
                select(ModelLifecycleEvent)
                .where(ModelLifecycleEvent.training_run_id == training_run_id)
                .order_by(ModelLifecycleEvent.created_at.desc())
                .limit(limit)
            ).scalars().all()
        )
