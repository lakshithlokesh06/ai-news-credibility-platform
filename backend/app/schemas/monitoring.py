from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.training import ClassicalModelType, ModelFamily


class MonitoringConfig(BaseModel):
    window_size: int = Field(default=100, ge=5, le=500)
    minimum_sample_count: int = Field(default=10, ge=2, le=100)
    low_confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    high_confidence_threshold: float = Field(default=0.90, ge=0.0, le=1.0)
    psi_warning_threshold: float = Field(default=0.10, ge=0.0, le=1.0)
    psi_drift_threshold: float = Field(default=0.25, ge=0.0, le=2.0)
    js_warning_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    js_drift_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    ks_warning_threshold: float = Field(default=0.20, ge=0.0, le=1.0)
    ks_drift_threshold: float = Field(default=0.35, ge=0.0, le=1.0)


class MonitoringProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    training_run_id: UUID
    profile_version: str
    status: str
    sample_count: int
    reference_statistics: dict
    reference_label_distribution: dict
    feature_metadata: dict
    created_at: datetime
    updated_at: datetime


class MonitoringMetric(BaseModel):
    metric_name: str
    metric_value: float | None
    warning_threshold: float | None = None
    drift_threshold: float | None = None
    status: str
    interpretation: str


class ConfidenceMonitoring(BaseModel):
    average_confidence: float | None
    median_confidence: float | None
    low_confidence_rate: float | None
    high_confidence_rate: float | None
    average_real_probability: float | None
    average_fake_probability: float | None
    confidence_distribution: list[int]
    confidence_shift: MonitoringMetric


class UsageMonitoring(BaseModel):
    total_analyses: int
    analyses_in_window: int
    real_prediction_count: int
    fake_prediction_count: int
    explanation_generation_rate: float | None
    average_confidence: float | None
    last_used_at: datetime | None
    recent_volume: list[dict]


class ModelMonitoringResponse(BaseModel):
    training_run_id: UUID
    model_display_name: str
    model_family: ModelFamily
    model_type: ClassicalModelType
    model_name: str | None
    monitoring_window: dict
    reference_profile_status: str
    reference_profile: MonitoringProfileResponse | None
    sample_counts: dict
    input_drift_metrics: list[MonitoringMetric]
    prediction_drift: MonitoringMetric
    confidence_metrics: ConfidenceMonitoring
    usage_metrics: UsageMonitoring
    overall_status: str
    status_reasons: list[str]
    limitations: list[str]


class MonitoringOverviewItem(BaseModel):
    training_run_id: UUID
    model_display_name: str
    model_family: ModelFamily
    model_type: ClassicalModelType
    model_name: str | None
    recent_analysis_count: int
    monitoring_status: str
    prediction_drift_status: str
    input_drift_status: str
    average_confidence: float | None
    last_analyzed_at: datetime | None


class MonitoringOverviewResponse(BaseModel):
    items: list[MonitoringOverviewItem]
    total_completed_models: int
    healthy_models: int
    models_needing_attention: int
    insufficient_data_models: int
    recent_analyses: int
    limitations: list[str]
