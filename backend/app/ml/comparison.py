from sqlalchemy.orm import Session

from app.models.training import ClassicalModelType, ModelFamily, TrainingRunStatus
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.experiments import ExperimentComparisonRequest
from app.schemas.ml import ModelComparisonItem, ModelComparisonResponse
from app.services.experiments import ExperimentService


class ModelComparisonService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TrainingRunRepository(db)

    def compare(
        self,
        *,
        metric_source: str = "test",
        primary_metric: str = "f1",
    ) -> ModelComparisonResponse:
        runs, _total = self.repository.list_runs(status=TrainingRunStatus.COMPLETED, limit=100, offset=0)
        items: list[ModelComparisonItem] = []
        detailed_comparison = None
        if len(runs) >= 2:
            detailed_comparison = ExperimentService(self.db).compare(
                ExperimentComparisonRequest(
                    training_run_ids=[run.id for run in runs[:4]],
                    metric_source=metric_source,  # type: ignore[arg-type]
                    primary_metric=primary_metric,  # type: ignore[arg-type]
                )
            )
            comparison_by_id = {item.training_run_id: item for item in detailed_comparison.items}
        else:
            comparison_by_id = {}
        for run in runs:
            metrics = run.test_metrics if metric_source == "test" else run.validation_metrics
            metric_value = metrics.get(primary_metric) if metrics else None
            comparison_item = comparison_by_id.get(run.id)
            items.append(
                ModelComparisonItem(
                    training_run_id=run.id,
                    model_display_name=run.model_display_name,
                    model_family=ModelFamily(run.model_family),
                    model_type=ClassicalModelType(run.model_type),
                    base_model_name=run.base_model_name,
                    explainability_supported=run.explainability_supported,
                    explanation_method=run.explanation_method,
                    status=TrainingRunStatus(run.status),
                    validation_metrics=run.validation_metrics,
                    test_metrics=run.test_metrics,
                    primary_metric_name=f"{metric_source}_{primary_metric}",
                    primary_metric_value=metric_value if isinstance(metric_value, float | int) else None,
                    lifecycle_status=run.lifecycle_status,
                    is_champion=run.lifecycle_status == "champion",
                    dataset_identifiers=run.dataset_identifiers,
                    text_composition_mode=(run.text_composition_config or {}).get("mode"),
                    rank=comparison_item.rank if comparison_item else None,
                    comparability_status=detailed_comparison.comparability_status if detailed_comparison else "directly_comparable",
                    comparability_warnings=detailed_comparison.comparability_warnings if detailed_comparison else [],
                )
            )

        ranked = [
            item
            for item in items
            if item.primary_metric_value is not None
            and item.comparability_status == "directly_comparable"
        ]
        recommended = max(ranked, key=lambda item: item.primary_metric_value).training_run_id if ranked else None
        note = (
            f"Recommendation is based only on directly comparable {metric_source} {primary_metric}."
            if recommended is not None
            else "No recommendation is made when experiments are missing metrics or have limited comparability."
        )
        return ModelComparisonResponse(
            metric_source=metric_source,
            primary_metric=primary_metric,
            items=items,
            recommended_training_run_id=recommended,
            recommendation_note=note,
            comparability_status=detailed_comparison.comparability_status if detailed_comparison else "directly_comparable",
            comparability_warnings=detailed_comparison.comparability_warnings if detailed_comparison else [],
        )
