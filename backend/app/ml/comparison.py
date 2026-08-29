from sqlalchemy.orm import Session

from app.models.training import ClassicalModelType, ModelFamily, TrainingRunStatus
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.ml import ModelComparisonItem, ModelComparisonResponse


class ModelComparisonService:
    def __init__(self, db: Session) -> None:
        self.repository = TrainingRunRepository(db)

    def compare(
        self,
        *,
        metric_source: str = "test",
        primary_metric: str = "f1",
    ) -> ModelComparisonResponse:
        runs, _total = self.repository.list_runs(status=TrainingRunStatus.COMPLETED, limit=100, offset=0)
        items: list[ModelComparisonItem] = []
        for run in runs:
            metrics = run.test_metrics if metric_source == "test" else run.validation_metrics
            metric_value = metrics.get(primary_metric) if metrics else None
            items.append(
                ModelComparisonItem(
                    training_run_id=run.id,
                    model_display_name=run.model_display_name,
                    model_family=ModelFamily(run.model_family),
                    model_type=ClassicalModelType(run.model_type),
                    base_model_name=run.base_model_name,
                    status=TrainingRunStatus(run.status),
                    validation_metrics=run.validation_metrics,
                    test_metrics=run.test_metrics,
                    primary_metric_name=f"{metric_source}_{primary_metric}",
                    primary_metric_value=metric_value if isinstance(metric_value, float | int) else None,
                )
            )

        ranked = [item for item in items if item.primary_metric_value is not None]
        recommended = max(ranked, key=lambda item: item.primary_metric_value).training_run_id if ranked else None
        note = (
            f"Recommendation is based only on {metric_source} {primary_metric}."
            if recommended is not None
            else None
        )
        return ModelComparisonResponse(
            metric_source=metric_source,
            primary_metric=primary_metric,
            items=items,
            recommended_training_run_id=recommended,
            recommendation_note=note,
        )
