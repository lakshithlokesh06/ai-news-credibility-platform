from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.training import ClassicalModelType, ModelFamily, ModelLifecycleStatus, TrainingRunStatus

MetricName = Literal["accuracy", "precision", "recall", "f1", "roc_auc"]
MetricSource = Literal["validation", "test"]
ComparabilityStatus = Literal["directly_comparable", "limited_comparability", "insufficient_metrics"]


class LifecycleEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    training_run_id: UUID
    previous_champion_id: UUID | None
    event_type: str
    from_status: str | None
    to_status: str | None
    note: str | None
    created_at: datetime


class ExperimentSummary(BaseModel):
    training_run_id: UUID
    model_display_name: str
    description: str | None
    tags: list[str]
    model_family: ModelFamily
    model_type: ClassicalModelType
    base_model_name: str | None
    execution_status: TrainingRunStatus
    lifecycle_status: ModelLifecycleStatus | None
    is_champion: bool
    dataset_identifiers: list[str]
    text_composition_mode: str | None
    random_seed: int
    train_count: int
    validation_count: int
    test_count: int
    primary_test_metric: float | None
    artifact_version: str | None
    artifact_checksum: str | None
    explainability_supported: bool
    explanation_method: str | None
    monitoring_available: bool
    trained_at: datetime | None
    created_at: datetime


class ExperimentDetail(ExperimentSummary):
    preprocessing_config: dict
    text_composition_config: dict
    tfidf_config: dict
    transformer_config: dict
    model_hyperparameters: dict
    split_config: dict
    split_distributions: dict
    validation_metrics: dict | None
    test_metrics: dict | None
    artifact_path: str | None
    probability_method: str | None
    device_used: str | None
    training_duration_seconds: float | None
    environment_versions: dict
    champion_promoted_at: datetime | None
    lifecycle_events: list[LifecycleEventResponse]


class PaginatedExperimentsResponse(BaseModel):
    items: list[ExperimentSummary]
    total: int
    limit: int
    offset: int


class ExperimentComparisonRequest(BaseModel):
    training_run_ids: list[UUID] = Field(min_length=2, max_length=4)
    primary_metric: MetricName = "f1"
    metric_source: MetricSource = "test"


class ExperimentComparisonItem(BaseModel):
    training_run_id: UUID
    model_display_name: str
    model_family: ModelFamily
    model_type: ClassicalModelType
    base_model_name: str | None
    lifecycle_status: ModelLifecycleStatus | None
    is_champion: bool
    dataset_identifiers: list[str]
    text_composition_mode: str | None
    split_config: dict
    validation_metrics: dict | None
    test_metrics: dict | None
    training_duration_seconds: float | None
    primary_metric_name: str
    primary_metric_value: float | None
    rank: int | None
    difference_from_best: float | None


class ExperimentComparisonResponse(BaseModel):
    metric_source: MetricSource
    primary_metric: MetricName
    comparability_status: ComparabilityStatus
    comparability_warnings: list[str]
    champion_training_run_id: UUID | None
    items: list[ExperimentComparisonItem]


class ChampionResponse(BaseModel):
    champion: ExperimentSummary | None


class LifecycleActionResponse(BaseModel):
    training_run_id: UUID
    lifecycle_status: ModelLifecycleStatus | None
    previous_champion_id: UUID | None = None
    message: str
