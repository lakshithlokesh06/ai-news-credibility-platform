from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily, ModelLifecycleStatus, TrainingRunStatus
from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig


class TfidfConfig(BaseModel):
    max_features: int = Field(default=5000, ge=100, le=100000)
    ngram_min: int = Field(default=1, ge=1, le=3)
    ngram_max: int = Field(default=2, ge=1, le=3)
    min_df: int = Field(default=1, ge=1)
    max_df: float = Field(default=0.95, gt=0, le=1)
    sublinear_tf: bool = True
    lowercase: bool = False

    @model_validator(mode="after")
    def validate_ngram_range(self) -> "TfidfConfig":
        if self.ngram_min > self.ngram_max:
            raise ValueError("ngram_min cannot be greater than ngram_max.")
        return self

    @property
    def ngram_range(self) -> tuple[int, int]:
        return (self.ngram_min, self.ngram_max)


class SplitConfig(BaseModel):
    train_ratio: float = Field(default=0.70, gt=0, lt=1)
    validation_ratio: float = Field(default=0.15, gt=0, lt=1)
    test_ratio: float = Field(default=0.15, gt=0, lt=1)

    @model_validator(mode="after")
    def validate_sum(self) -> "SplitConfig":
        total = self.train_ratio + self.validation_ratio + self.test_ratio
        if abs(total - 1.0) > 0.0001:
            raise ValueError("Split ratios must sum to 1.0.")
        return self


class ModelHyperparameters(BaseModel):
    c: float = Field(default=1.0, gt=0, le=1000)
    max_iter: int = Field(default=1000, ge=100, le=20000)
    class_weight: str | None = "balanced"
    calibration_cv: int = Field(default=3, ge=2, le=5)


class TransformerConfig(BaseModel):
    model_name: str = Field(default="distilbert-base-uncased", min_length=1, max_length=255)
    max_sequence_length: int = Field(default=192, ge=32, le=512)
    batch_size: int = Field(default=4, ge=1, le=32)
    learning_rate: float = Field(default=2e-5, gt=0, le=1e-3)
    epochs: float = Field(default=1.0, gt=0, le=10)
    weight_decay: float = Field(default=0.01, ge=0, le=1)
    evaluation_strategy: str = Field(default="epoch", pattern="^(no|epoch)$")
    device_preference: str = Field(default="auto", pattern="^(auto|mps|cuda|cpu)$")


class TrainingRunCreate(BaseModel):
    model_type: ClassicalModelType
    model_display_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    dataset_names: list[str] | None = Field(default=None, max_length=20)
    text_composition: TextCompositionConfig = Field(default_factory=TextCompositionConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    tfidf: TfidfConfig = Field(default_factory=TfidfConfig)
    transformer: TransformerConfig = Field(default_factory=TransformerConfig)
    split: SplitConfig = Field(default_factory=SplitConfig)
    hyperparameters: ModelHyperparameters = Field(default_factory=ModelHyperparameters)
    random_seed: int = Field(default=42, ge=0, le=2_147_483_647)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        normalized = []
        seen = set()
        for tag in value:
            cleaned = tag.strip()
            if not cleaned:
                continue
            if len(cleaned) > 64:
                raise ValueError("Tags must be 64 characters or fewer.")
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                normalized.append(cleaned)
        return normalized

    @property
    def model_family(self) -> ModelFamily:
        return (
            ModelFamily.TRANSFORMER
            if self.model_type == ClassicalModelType.DISTILBERT
            else ModelFamily.CLASSICAL
        )


class MetricSet(BaseModel):
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    roc_auc: float | None
    confusion_matrix: list[list[int]]
    class_metrics: dict[str, dict[str, float | int | None]]
    support: dict[str, int]


class MLTrainingRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_family: ModelFamily
    model_type: ClassicalModelType
    base_model_name: str | None
    model_display_name: str
    description: str | None
    tags: list[str]
    explainability_supported: bool
    explanation_method: str | None
    status: TrainingRunStatus
    lifecycle_status: ModelLifecycleStatus | None
    preprocessing_config: dict
    text_composition_config: dict
    tfidf_config: dict
    transformer_config: dict
    model_hyperparameters: dict
    split_config: dict
    random_seed: int
    train_count: int
    validation_count: int
    test_count: int
    dataset_article_count: int
    dataset_identifiers: list[str]
    split_distributions: dict
    validation_metrics: dict | None
    test_metrics: dict | None
    artifact_path: str | None
    artifact_checksum: str | None
    artifact_version: str | None
    probability_method: str | None
    device_used: str | None
    training_duration_seconds: float | None
    environment_versions: dict
    champion_promoted_at: datetime | None
    error_summary: str | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime


class PaginatedTrainingRunsResponse(BaseModel):
    items: list[MLTrainingRunResponse]
    total: int
    limit: int
    offset: int


class PredictionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=settings.max_article_title_chars)
    content: str | None = Field(default=None, max_length=settings.max_article_content_chars)
    save_to_history: bool = False

    @model_validator(mode="after")
    def validate_article_size(self) -> "PredictionRequest":
        title_length = len(self.title or "")
        content_length = len(self.content or "")
        if title_length + content_length > settings.max_combined_article_chars:
            raise ValueError(
                f"Combined title and content must be {settings.max_combined_article_chars} characters or fewer."
            )
        return self


class ExplanationConfig(BaseModel):
    max_items: int = Field(default=8, ge=1, le=25)
    method: str = Field(default="auto", pattern="^(auto|coefficient|shap)$")
    max_transformer_length: int = Field(default=128, ge=16, le=256)
    max_evaluations: int = Field(default=16, ge=2, le=64)
    include_real_support: bool = True
    include_fake_support: bool = True


class ExplanationRequest(PredictionRequest):
    explanation: ExplanationConfig = Field(default_factory=ExplanationConfig)
    analysis_id: UUID | None = None


class PredictionResponse(BaseModel):
    training_run_id: UUID
    analysis_id: UUID | None = None
    model_family: ModelFamily
    model_type: ClassicalModelType
    model_name: str | None
    predicted_label: ArticleLabel
    real_probability: float | None
    fake_probability: float | None
    confidence: float | None
    probability_method: str | None
    message: str


class InfluentialItem(BaseModel):
    text: str
    attribution_score: float
    attribution_magnitude: float
    direction: ArticleLabel
    rank: int
    start_offset: int | None = None
    end_offset: int | None = None
    source_tokens: list[str] | None = None


class ExplanationResponse(BaseModel):
    training_run_id: UUID
    analysis_id: UUID | None = None
    model_family: ModelFamily
    model_type: ClassicalModelType
    model_name: str | None
    predicted_label: ArticleLabel
    real_probability: float | None
    fake_probability: float | None
    confidence: float | None
    probability_method: str | None
    explanation_method: str
    explained_class: ArticleLabel
    influences_toward_real: list[InfluentialItem]
    influences_toward_fake: list[InfluentialItem]
    limitations: list[str]
    message: str


class ModelComparisonItem(BaseModel):
    training_run_id: UUID
    model_display_name: str
    model_family: ModelFamily
    model_type: ClassicalModelType
    base_model_name: str | None
    explainability_supported: bool
    explanation_method: str | None
    status: TrainingRunStatus
    validation_metrics: dict | None
    test_metrics: dict | None
    primary_metric_name: str
    primary_metric_value: float | None
    lifecycle_status: str | None = None
    is_champion: bool = False
    dataset_identifiers: list[str] = Field(default_factory=list)
    text_composition_mode: str | None = None
    rank: int | None = None
    comparability_status: str = "directly_comparable"
    comparability_warnings: list[str] = Field(default_factory=list)


class ModelComparisonResponse(BaseModel):
    metric_source: str
    primary_metric: str
    items: list[ModelComparisonItem]
    recommended_training_run_id: UUID | None
    recommendation_note: str | None
    comparability_status: str = "directly_comparable"
    comparability_warnings: list[str] = Field(default_factory=list)
