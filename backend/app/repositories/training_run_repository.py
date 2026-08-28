from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.training import MLTrainingRun, TrainingRunStatus


class TrainingRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, training_run: MLTrainingRun) -> MLTrainingRun:
        self.db.add(training_run)
        return training_run

    def get(self, training_run_id: UUID) -> MLTrainingRun | None:
        return self.db.get(MLTrainingRun, training_run_id)

    def list_runs(
        self,
        *,
        status: TrainingRunStatus | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[MLTrainingRun], int]:
        statement = select(MLTrainingRun)
        count_statement = select(func.count()).select_from(MLTrainingRun)
        if status is not None:
            statement = statement.where(MLTrainingRun.status == status.value)
            count_statement = count_statement.where(MLTrainingRun.status == status.value)

        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(
            statement.order_by(MLTrainingRun.started_at.desc()).limit(limit).offset(offset)
        ).scalars().all()
        return list(items), int(total)

