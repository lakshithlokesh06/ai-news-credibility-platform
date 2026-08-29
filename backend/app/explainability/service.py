from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.explainability.classical import ClassicalExplainer
from app.explainability.config import ExplanationError
from app.explainability.transformer import TransformerExplainer
from app.ml.artifacts import ArtifactStore
from app.ml.inference import InferenceError, InferenceService
from app.models.training import ModelFamily, TrainingRunStatus
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.ml import ExplanationRequest, ExplanationResponse


class ExplanationService:
    def __init__(self, db: Session, artifact_base_dir: Path | None = None) -> None:
        self.repository = TrainingRunRepository(db)
        self.artifact_store = ArtifactStore(artifact_base_dir)
        self.inference = InferenceService(db, artifact_base_dir=artifact_base_dir)

    def explain(self, training_run_id: UUID, request: ExplanationRequest) -> ExplanationResponse:
        training_run = self.repository.get(training_run_id)
        if training_run is None:
            raise ExplanationError("Training run was not found.", "missing_training_run")
        if training_run.status != TrainingRunStatus.COMPLETED.value:
            raise ExplanationError("Only completed training runs can be explained.", "incomplete_training_run")
        if not training_run.artifact_path:
            raise ExplanationError("Training run does not have a model artifact.", "missing_artifact")
        if not training_run.explainability_supported:
            raise ExplanationError("This model type does not support explanations.", "unsupported_model_type")

        try:
            prediction = self.inference.predict(training_run_id, request)
        except InferenceError as exc:
            raise ExplanationError(str(exc), "prediction_failed") from exc

        if training_run.model_family == ModelFamily.TRANSFORMER.value:
            return TransformerExplainer(self.artifact_store.base_dir).explain(training_run, request, prediction)

        if training_run.model_family == ModelFamily.CLASSICAL.value:
            return ClassicalExplainer(self.artifact_store).explain(training_run, request, prediction)

        raise ExplanationError("This model family does not support explanations.", "unsupported_model_family")
