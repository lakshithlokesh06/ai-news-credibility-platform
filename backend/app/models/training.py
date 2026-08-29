import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base


class ClassicalModelType(StrEnum):
    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR_SVM = "linear_svm"
    DISTILBERT = "distilbert"


class ModelFamily(StrEnum):
    CLASSICAL = "classical"
    TRANSFORMER = "transformer"


class TrainingRunStatus(StrEnum):
    PENDING = "pending"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class MLTrainingRun(Base):
    __tablename__ = "ml_training_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_family: Mapped[str] = mapped_column(String(32), nullable=False, default=ModelFamily.CLASSICAL.value, index=True)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    base_model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    preprocessing_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    text_composition_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    tfidf_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    transformer_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    model_hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    split_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    random_seed: Mapped[int] = mapped_column(nullable=False)
    train_count: Mapped[int] = mapped_column(default=0, nullable=False)
    validation_count: Mapped[int] = mapped_column(default=0, nullable=False)
    test_count: Mapped[int] = mapped_column(default=0, nullable=False)
    dataset_article_count: Mapped[int] = mapped_column(default=0, nullable=False)
    dataset_identifiers: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    split_distributions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    validation_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    test_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    artifact_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    probability_method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_used: Mapped[str | None] = mapped_column(String(64), nullable=True)
    training_duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_ml_training_runs_status_started", "status", "started_at"),
        Index("ix_ml_training_runs_family_status", "model_family", "status"),
        Index("ix_ml_training_runs_model_status", "model_type", "status"),
    )

    @property
    def explanation_method(self) -> str | None:
        try:
            return explanation_method_for_type(ClassicalModelType(self.model_type))
        except ValueError:
            return None

    @property
    def explainability_supported(self) -> bool:
        return (
            self.status == TrainingRunStatus.COMPLETED.value
            and bool(self.artifact_path)
            and self.explanation_method is not None
        )


def model_family_for_type(model_type: ClassicalModelType) -> ModelFamily:
    if model_type == ClassicalModelType.DISTILBERT:
        return ModelFamily.TRANSFORMER
    return ModelFamily.CLASSICAL


def explanation_method_for_type(model_type: ClassicalModelType) -> str | None:
    if model_type == ClassicalModelType.LOGISTIC_REGRESSION:
        return "coefficient_tfidf_local_or_shap"
    if model_type == ClassicalModelType.LINEAR_SVM:
        return "linear_svm_underlying_decision_function"
    if model_type == ClassicalModelType.DISTILBERT:
        return "shap_text"
    return None
