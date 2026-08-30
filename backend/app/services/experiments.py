from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ml.artifacts import ArtifactError, ArtifactStore
from app.ml.transformer_artifacts import TransformerArtifactStore
from app.models.lifecycle import ModelLifecycleEvent, ModelLifecycleEventType
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, ModelLifecycleStatus, TrainingRunStatus
from app.repositories.lifecycle_repository import ModelLifecycleEventRepository
from app.repositories.monitoring_repository import MonitoringProfileRepository
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.experiments import (
    ChampionResponse,
    ComparabilityStatus,
    ExperimentComparisonItem,
    ExperimentComparisonRequest,
    ExperimentComparisonResponse,
    ExperimentDetail,
    ExperimentSummary,
    LifecycleActionResponse,
    LifecycleEventResponse,
    MetricName,
    MetricSource,
    PaginatedExperimentsResponse,
)


class ExperimentError(ValueError):
    def __init__(self, message: str, error_type: str = "experiment_error") -> None:
        super().__init__(message)
        self.error_type = error_type


class ExperimentService:
    def __init__(self, db: Session, artifact_base_dir: Path | None = None) -> None:
        self.db = db
        self.artifact_base_dir = artifact_base_dir
        self.training_runs = TrainingRunRepository(db)
        self.lifecycle_events = ModelLifecycleEventRepository(db)
        self.monitoring_profiles = MonitoringProfileRepository(db)

    def list_experiments(
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
    ) -> PaginatedExperimentsResponse:
        runs, total = self.training_runs.list_runs(
            status=status,
            model_family=model_family,
            model_type=model_type,
            lifecycle_status=lifecycle_status,
            champion=champion,
            trained_after=trained_after,
            trained_before=trained_before,
            limit=limit,
            offset=offset,
        )
        return PaginatedExperimentsResponse(
            items=[self._summary(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_experiment(self, training_run_id: UUID) -> ExperimentDetail:
        run = self._get_run(training_run_id)
        return self._detail(run)

    def get_champion(self) -> ChampionResponse:
        champion = self.training_runs.get_champion()
        return ChampionResponse(champion=self._summary(champion) if champion else None)

    def promote(self, training_run_id: UUID) -> LifecycleActionResponse:
        target = self._validate_champion_candidate(training_run_id)
        existing = self.training_runs.get_champion()
        if existing and existing.id == target.id:
            return LifecycleActionResponse(
                training_run_id=target.id,
                lifecycle_status=ModelLifecycleStatus.CHAMPION,
                previous_champion_id=None,
                message="Model is already the champion.",
            )

        now = datetime.now(UTC)
        previous_id = existing.id if existing else None
        try:
            if existing is not None:
                from_status = existing.lifecycle_status
                existing.lifecycle_status = ModelLifecycleStatus.CANDIDATE.value
                existing.champion_promoted_at = None
                self.lifecycle_events.add(
                    ModelLifecycleEvent(
                        training_run_id=existing.id,
                        previous_champion_id=target.id,
                        event_type=ModelLifecycleEventType.DEMOTED.value,
                        from_status=from_status,
                        to_status=ModelLifecycleStatus.CANDIDATE.value,
                        note="Demoted during champion promotion.",
                        created_at=now,
                    )
                )
                self.db.flush()

            from_status = target.lifecycle_status
            target.lifecycle_status = ModelLifecycleStatus.CHAMPION.value
            target.champion_promoted_at = now
            self.lifecycle_events.add(
                ModelLifecycleEvent(
                    training_run_id=target.id,
                    previous_champion_id=previous_id,
                    event_type=ModelLifecycleEventType.PROMOTED.value,
                    from_status=from_status,
                    to_status=ModelLifecycleStatus.CHAMPION.value,
                    note="Promoted to application champion.",
                    created_at=now,
                )
            )
            self.db.commit()
            self.db.refresh(target)
        except IntegrityError as exc:
            self.db.rollback()
            raise ExperimentError("Champion promotion would violate the single-champion constraint.", "champion_conflict") from exc
        except Exception:
            self.db.rollback()
            raise

        return LifecycleActionResponse(
            training_run_id=target.id,
            lifecycle_status=ModelLifecycleStatus.CHAMPION,
            previous_champion_id=previous_id,
            message="Model promoted to champion.",
        )

    def archive(self, training_run_id: UUID) -> LifecycleActionResponse:
        run = self._get_run(training_run_id)
        if run.lifecycle_status == ModelLifecycleStatus.CHAMPION.value:
            raise ExperimentError("The active champion cannot be archived. Promote another model first.", "cannot_archive_champion")
        if run.status != TrainingRunStatus.COMPLETED.value:
            raise ExperimentError("Only completed models can be archived.", "ineligible_lifecycle_action")
        if run.lifecycle_status == ModelLifecycleStatus.ARCHIVED.value:
            return LifecycleActionResponse(
                training_run_id=run.id,
                lifecycle_status=ModelLifecycleStatus.ARCHIVED,
                message="Model is already archived.",
            )
        from_status = run.lifecycle_status
        run.lifecycle_status = ModelLifecycleStatus.ARCHIVED.value
        self.lifecycle_events.add(
            ModelLifecycleEvent(
                training_run_id=run.id,
                event_type=ModelLifecycleEventType.ARCHIVED.value,
                from_status=from_status,
                to_status=ModelLifecycleStatus.ARCHIVED.value,
                note="Archived from active experiment views.",
                created_at=datetime.now(UTC),
            )
        )
        self.db.commit()
        return LifecycleActionResponse(
            training_run_id=run.id,
            lifecycle_status=ModelLifecycleStatus.ARCHIVED,
            message="Model archived. Metrics, artifacts, monitoring, and history were preserved.",
        )

    def restore(self, training_run_id: UUID) -> LifecycleActionResponse:
        run = self._validate_champion_candidate(training_run_id, allow_archived=True)
        if run.lifecycle_status != ModelLifecycleStatus.ARCHIVED.value:
            return LifecycleActionResponse(
                training_run_id=run.id,
                lifecycle_status=ModelLifecycleStatus(run.lifecycle_status) if run.lifecycle_status else None,
                message="Model is already active.",
            )
        from_status = run.lifecycle_status
        run.lifecycle_status = ModelLifecycleStatus.CANDIDATE.value
        self.lifecycle_events.add(
            ModelLifecycleEvent(
                training_run_id=run.id,
                event_type=ModelLifecycleEventType.RESTORED.value,
                from_status=from_status,
                to_status=ModelLifecycleStatus.CANDIDATE.value,
                note="Restored to candidate lifecycle status.",
                created_at=datetime.now(UTC),
            )
        )
        self.db.commit()
        return LifecycleActionResponse(
            training_run_id=run.id,
            lifecycle_status=ModelLifecycleStatus.CANDIDATE,
            message="Model restored to candidate status.",
        )

    def compare(self, request: ExperimentComparisonRequest) -> ExperimentComparisonResponse:
        runs = self.training_runs.list_by_ids(request.training_run_ids)
        run_by_id = {run.id: run for run in runs}
        missing = [run_id for run_id in request.training_run_ids if run_id not in run_by_id]
        if missing:
            raise ExperimentError("One or more selected training runs were not found.", "missing_training_run")
        ordered_runs = [run_by_id[run_id] for run_id in request.training_run_ids]
        warnings = _comparability_warnings(ordered_runs)
        status: ComparabilityStatus = "limited_comparability" if warnings else "directly_comparable"
        values = [_metric_value(run, request.metric_source, request.primary_metric) for run in ordered_runs]
        if any(value is None for value in values):
            status = "insufficient_metrics"
            warnings.append("One or more selected experiments is missing the requested persisted metric.")

        best_value = max((value for value in values if value is not None), default=None)
        ranks = _ranks(values) if status == "directly_comparable" else [None for _run in ordered_runs]
        items = [
            ExperimentComparisonItem(
                training_run_id=run.id,
                model_display_name=run.model_display_name,
                model_family=ModelFamily(run.model_family),
                model_type=ClassicalModelType(run.model_type),
                base_model_name=run.base_model_name,
                lifecycle_status=ModelLifecycleStatus(run.lifecycle_status) if run.lifecycle_status else None,
                is_champion=run.lifecycle_status == ModelLifecycleStatus.CHAMPION.value,
                dataset_identifiers=run.dataset_identifiers,
                text_composition_mode=(run.text_composition_config or {}).get("mode"),
                split_config=run.split_config,
                validation_metrics=run.validation_metrics,
                test_metrics=run.test_metrics,
                training_duration_seconds=run.training_duration_seconds,
                primary_metric_name=f"{request.metric_source}_{request.primary_metric}",
                primary_metric_value=value,
                rank=rank,
                difference_from_best=round(float(best_value - value), 6) if best_value is not None and value is not None else None,
            )
            for run, value, rank in zip(ordered_runs, values, ranks, strict=True)
        ]
        champion = self.training_runs.get_champion()
        return ExperimentComparisonResponse(
            metric_source=request.metric_source,
            primary_metric=request.primary_metric,
            comparability_status=status,
            comparability_warnings=warnings,
            champion_training_run_id=champion.id if champion else None,
            items=items,
        )

    def _get_run(self, training_run_id: UUID) -> MLTrainingRun:
        run = self.training_runs.get(training_run_id)
        if run is None:
            raise ExperimentError("Training run was not found.", "missing_training_run")
        return run

    def _validate_champion_candidate(self, training_run_id: UUID, *, allow_archived: bool = False) -> MLTrainingRun:
        run = self._get_run(training_run_id)
        if run.status != TrainingRunStatus.COMPLETED.value:
            raise ExperimentError("Only completed training runs can be promoted or restored.", "incomplete_training_run")
        if run.lifecycle_status == ModelLifecycleStatus.ARCHIVED.value and not allow_archived:
            raise ExperimentError("Archived models must be restored before promotion.", "archived_model")
        if not run.artifact_path or not run.artifact_checksum or not run.artifact_version:
            raise ExperimentError("Model artifacts are required for champion selection.", "missing_artifact")
        if not run.validation_metrics or not run.test_metrics:
            raise ExperimentError("Validation and test metrics are required for champion selection.", "missing_metrics")
        try:
            if run.model_family == ModelFamily.TRANSFORMER.value:
                TransformerArtifactStore(self.artifact_base_dir).load_metadata(run.artifact_path)
            else:
                ArtifactStore(self.artifact_base_dir).load(run.artifact_path)
        except ArtifactError as exc:
            raise ExperimentError(str(exc), "invalid_artifact") from exc
        return run

    def _summary(self, run: MLTrainingRun) -> ExperimentSummary:
        return ExperimentSummary(
            training_run_id=run.id,
            model_display_name=run.model_display_name,
            description=run.description,
            tags=run.tags or [],
            model_family=ModelFamily(run.model_family),
            model_type=ClassicalModelType(run.model_type),
            base_model_name=run.base_model_name,
            execution_status=TrainingRunStatus(run.status),
            lifecycle_status=ModelLifecycleStatus(run.lifecycle_status) if run.lifecycle_status else None,
            is_champion=run.lifecycle_status == ModelLifecycleStatus.CHAMPION.value,
            dataset_identifiers=run.dataset_identifiers,
            text_composition_mode=(run.text_composition_config or {}).get("mode"),
            random_seed=run.random_seed,
            train_count=run.train_count,
            validation_count=run.validation_count,
            test_count=run.test_count,
            primary_test_metric=_metric_value(run, "test", "f1"),
            artifact_version=run.artifact_version,
            artifact_checksum=run.artifact_checksum,
            explainability_supported=run.explainability_supported,
            explanation_method=run.explanation_method,
            monitoring_available=self.monitoring_profiles.get_active(run.id) is not None,
            trained_at=run.completed_at,
            created_at=run.created_at,
        )

    def _detail(self, run: MLTrainingRun) -> ExperimentDetail:
        summary = self._summary(run)
        return ExperimentDetail(
            **summary.model_dump(),
            preprocessing_config=run.preprocessing_config,
            text_composition_config=run.text_composition_config,
            tfidf_config=run.tfidf_config,
            transformer_config=run.transformer_config,
            model_hyperparameters=run.model_hyperparameters,
            split_config=run.split_config,
            split_distributions=run.split_distributions,
            validation_metrics=run.validation_metrics,
            test_metrics=run.test_metrics,
            artifact_path=run.artifact_path,
            probability_method=run.probability_method,
            device_used=run.device_used,
            training_duration_seconds=run.training_duration_seconds,
            environment_versions=run.environment_versions or {},
            champion_promoted_at=run.champion_promoted_at,
            lifecycle_events=[
                LifecycleEventResponse.model_validate(event)
                for event in self.lifecycle_events.list_for_run(run.id)
            ],
        )


def _metric_value(run: MLTrainingRun, metric_source: MetricSource, metric_name: MetricName) -> float | None:
    metrics = run.test_metrics if metric_source == "test" else run.validation_metrics
    if not metrics:
        return None
    value = metrics.get(metric_name)
    return float(value) if isinstance(value, int | float) else None


def _comparability_warnings(runs: list[MLTrainingRun]) -> list[str]:
    if len(runs) < 2:
        return []
    warnings = []
    baseline = runs[0]
    if any(run.dataset_identifiers != baseline.dataset_identifiers for run in runs[1:]):
        warnings.append("Selected experiments used different dataset/import identifiers.")
    if any(run.split_config != baseline.split_config for run in runs[1:]):
        warnings.append("Selected experiments used different train/validation/test split configuration.")
    if any(run.text_composition_config != baseline.text_composition_config for run in runs[1:]):
        warnings.append("Selected experiments used different text composition configuration.")
    return warnings


def _ranks(values: list[float | None]) -> list[int | None]:
    present = sorted(
        [(index, value) for index, value in enumerate(values) if value is not None],
        key=lambda item: item[1],
        reverse=True,
    )
    ranks: list[int | None] = [None] * len(values)
    for rank, (index, _value) in enumerate(present, start=1):
        ranks[index] = rank
    return ranks
