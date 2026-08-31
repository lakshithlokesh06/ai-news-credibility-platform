from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily
from app.schemas.ml import InfluentialItem
from app.schemas.review import AnalysisReviewInfo


class AnalysisHistorySummary(BaseModel):
    id: UUID
    training_run_id: UUID | None
    model_family: ModelFamily
    model_type: ClassicalModelType
    model_name: str | None
    model_display_name: str
    title: str | None
    article_preview: str | None
    predicted_label: ArticleLabel
    real_probability: float | None
    fake_probability: float | None
    confidence: float | None
    explanation_available: bool
    explanation_method: str | None
    review: AnalysisReviewInfo
    created_at: datetime
    updated_at: datetime


class AnalysisExplanationDetail(BaseModel):
    explanation_method: str
    explained_class: ArticleLabel
    influences_toward_real: list[InfluentialItem]
    influences_toward_fake: list[InfluentialItem]
    limitations: list[str]
    message: str | None
    generated_at: datetime


class AnalysisHistoryDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    training_run_id: UUID | None
    model_family: ModelFamily
    model_type: ClassicalModelType
    model_name: str | None
    model_display_name: str
    title: str | None
    content: str | None
    text_composition_mode: str | None
    predicted_label: ArticleLabel
    real_probability: float | None
    fake_probability: float | None
    confidence: float | None
    probability_method: str | None
    explanation_status: str
    explanation: AnalysisExplanationDetail | None
    review: AnalysisReviewInfo
    created_at: datetime
    updated_at: datetime


class PaginatedHistoryResponse(BaseModel):
    items: list[AnalysisHistorySummary]
    total: int
    limit: int
    offset: int


class HistoryDistributionItem(BaseModel):
    name: str
    count: int
    percentage: float | None


class TrainingRunHistoryItem(BaseModel):
    training_run_id: UUID | None
    model_display_name: str
    count: int
    percentage: float | None


class RecentHistoryVolumeItem(BaseModel):
    date: str
    count: int


class HistoryStatisticsResponse(BaseModel):
    total_saved_analyses: int
    likely_real_count: int
    likely_fake_count: int
    likely_real_percentage: float | None
    likely_fake_percentage: float | None
    average_confidence: float | None
    average_real_confidence: float | None
    average_fake_confidence: float | None
    analyses_with_explanations: int
    analyses_without_explanations: int
    model_family_distribution: list[HistoryDistributionItem]
    model_type_distribution: list[HistoryDistributionItem]
    training_run_distribution: list[TrainingRunHistoryItem]
    recent_volume: list[RecentHistoryVolumeItem]
    interpretation: str


class DeleteHistoryResponse(BaseModel):
    analysis_id: UUID
    deleted: bool
    message: str
