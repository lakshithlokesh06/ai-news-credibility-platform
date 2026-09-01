from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily, ModelLifecycleStatus
from app.schemas.evidence import AnalysisEvidenceSummary

ReviewState = Literal["unreviewed", "reviewed"]
ReviewFilter = Literal["all", "unreviewed", "reviewed", "correct", "incorrect"]
ConfidenceBucket = Literal["all", "high", "low"]
QueueSort = Literal["recent", "low_confidence", "high_confidence"]
ErrorType = Literal["false_positive", "false_negative", "correct_real", "correct_fake"]
SufficiencyStatus = Literal["insufficient_data", "preliminary", "sufficient"]


class AnalysisReviewInfo(BaseModel):
    status: ReviewState
    review_id: UUID | None = None
    verified_label: ArticleLabel | None = None
    is_prediction_correct: bool | None = None
    reviewer_note: str | None = None
    evidence_note: str | None = None
    reviewed_at: datetime | None = None
    updated_at: datetime | None = None


class ReviewUpsertRequest(BaseModel):
    verified_label: ArticleLabel
    reviewer_note: str | None = Field(default=None, max_length=settings.review_note_max_chars)
    evidence_note: str | None = Field(default=None, max_length=settings.review_evidence_note_max_chars)

    @field_validator("reviewer_note", "evidence_note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None


class ReviewResponse(BaseModel):
    analysis_id: UUID
    review: AnalysisReviewInfo
    message: str


class DeleteReviewResponse(BaseModel):
    analysis_id: UUID
    deleted: bool
    message: str


class ReviewQueueItem(BaseModel):
    id: UUID
    training_run_id: UUID | None
    model_family: ModelFamily
    model_type: ClassicalModelType
    model_name: str | None
    model_display_name: str
    title: str | None
    article_preview: str | None
    predicted_label: ArticleLabel
    confidence: float | None
    explanation_available: bool
    review: AnalysisReviewInfo
    evidence_summary: AnalysisEvidenceSummary
    created_at: datetime


class PaginatedReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    total: int
    limit: int
    offset: int
    sort: QueueSort


class TrainingRunReviewSummary(BaseModel):
    training_run_id: UUID | None
    model_display_name: str
    model_family: ModelFamily | None
    model_type: ClassicalModelType | None
    lifecycle_status: ModelLifecycleStatus | None
    analysis_count: int
    reviewed_count: int
    correct_count: int
    incorrect_count: int
    review_coverage_percentage: float | None
    is_champion: bool


class ReviewStatisticsResponse(BaseModel):
    total_analyses: int
    reviewed_analyses: int
    unreviewed_analyses: int
    review_coverage_percentage: float | None
    reviewed_real_count: int
    reviewed_fake_count: int
    correct_prediction_count: int
    incorrect_prediction_count: int
    per_training_run: list[TrainingRunReviewSummary]
    interpretation: str


class ConfusionMatrixResponse(BaseModel):
    labels: list[ArticleLabel]
    matrix: list[list[int]]
    true_real_pred_real: int
    true_real_pred_fake: int
    true_fake_pred_real: int
    true_fake_pred_fake: int
    positive_class: ArticleLabel = ArticleLabel.FAKE


class RocAucResponse(BaseModel):
    value: float | None
    available: bool
    reason: str | None


class ProductionPerformanceResponse(BaseModel):
    scope: Literal["training_run", "mixed_model_aggregate"]
    training_run_id: UUID | None
    model_display_name: str
    model_family: ModelFamily | None
    model_type: ClassicalModelType | None
    reviewed_count: int
    correct_count: int
    incorrect_count: int
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    roc_auc: RocAucResponse
    confusion_matrix: ConfusionMatrixResponse
    minimum_reviewed_samples: int
    sufficiency_status: SufficiencyStatus
    positive_class: ArticleLabel = ArticleLabel.FAKE
    held_out_test_metrics: dict | None
    limitations: list[str]


class ReliabilityBin(BaseModel):
    lower_bound: float
    upper_bound: float
    sample_count: int
    mean_confidence: float
    observed_accuracy: float


class CalibrationResponse(BaseModel):
    scope: Literal["training_run", "mixed_model_aggregate"]
    training_run_id: UUID | None
    model_display_name: str
    sample_count: int
    bin_count: int
    brier_score: float | None
    expected_calibration_error: float | None
    reliability_bins: list[ReliabilityBin]
    minimum_reviewed_samples: int
    sufficiency_status: SufficiencyStatus
    limitations: list[str]


class ErrorAnalysisItem(BaseModel):
    analysis_id: UUID
    training_run_id: UUID | None
    model_display_name: str
    title: str | None
    article_preview: str | None
    predicted_label: ArticleLabel
    verified_label: ArticleLabel
    confidence: float | None
    error_type: ErrorType
    explanation_available: bool
    created_at: datetime
    reviewed_at: datetime


class ErrorConfidenceStatistics(BaseModel):
    average_confidence_correct: float | None
    average_confidence_incorrect: float | None
    high_confidence_error_count: int
    high_confidence_error_rate: float | None
    low_confidence_error_count: int
    low_confidence_error_rate: float | None
    high_confidence_threshold: float
    low_confidence_threshold: float


class ErrorAnalysisResponse(BaseModel):
    items: list[ErrorAnalysisItem]
    total: int
    limit: int
    offset: int
    statistics: ErrorConfidenceStatistics
    definitions: dict[str, str]
