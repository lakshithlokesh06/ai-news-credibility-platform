from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, ModelLifecycleStatus, TrainingRunStatus


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
        model_family: ModelFamily | None = None,
        model_type: ClassicalModelType | None = None,
        lifecycle_status: ModelLifecycleStatus | None = None,
        champion: bool | None = None,
        trained_after=None,
        trained_before=None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[MLTrainingRun], int]:
        statement = select(MLTrainingRun)
        count_statement = select(func.count()).select_from(MLTrainingRun)
        if status is not None:
            statement = statement.where(MLTrainingRun.status == status.value)
            count_statement = count_statement.where(MLTrainingRun.status == status.value)
        if model_family is not None:
            statement = statement.where(MLTrainingRun.model_family == model_family.value)
            count_statement = count_statement.where(MLTrainingRun.model_family == model_family.value)
        if model_type is not None:
            statement = statement.where(MLTrainingRun.model_type == model_type.value)
            count_statement = count_statement.where(MLTrainingRun.model_type == model_type.value)
        if lifecycle_status is not None:
            statement = statement.where(MLTrainingRun.lifecycle_status == lifecycle_status.value)
            count_statement = count_statement.where(MLTrainingRun.lifecycle_status == lifecycle_status.value)
        if champion is True:
            statement = statement.where(MLTrainingRun.lifecycle_status == ModelLifecycleStatus.CHAMPION.value)
            count_statement = count_statement.where(MLTrainingRun.lifecycle_status == ModelLifecycleStatus.CHAMPION.value)
        elif champion is False:
            statement = statement.where(MLTrainingRun.lifecycle_status != ModelLifecycleStatus.CHAMPION.value)
            count_statement = count_statement.where(MLTrainingRun.lifecycle_status != ModelLifecycleStatus.CHAMPION.value)
        if trained_after is not None:
            statement = statement.where(MLTrainingRun.completed_at >= trained_after)
            count_statement = count_statement.where(MLTrainingRun.completed_at >= trained_after)
        if trained_before is not None:
            statement = statement.where(MLTrainingRun.completed_at <= trained_before)
            count_statement = count_statement.where(MLTrainingRun.completed_at <= trained_before)

        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(
            statement.order_by(MLTrainingRun.started_at.desc()).limit(limit).offset(offset)
        ).scalars().all()
        return list(items), int(total)

    def get_champion(self) -> MLTrainingRun | None:
        return self.db.execute(
            select(MLTrainingRun).where(MLTrainingRun.lifecycle_status == ModelLifecycleStatus.CHAMPION.value)
        ).scalars().first()

    def list_by_ids(self, training_run_ids: list[UUID]) -> list[MLTrainingRun]:
        if not training_run_ids:
            return []
        return list(
            self.db.execute(
                select(MLTrainingRun).where(MLTrainingRun.id.in_(training_run_ids))
            ).scalars().all()
        )
