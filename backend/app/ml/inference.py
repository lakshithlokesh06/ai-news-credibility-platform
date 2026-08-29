from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily, TrainingRunStatus
from app.ml.artifacts import ArtifactError, ArtifactStore
from app.ml.transformer_inference import TransformerInferenceService
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.ml import PredictionRequest, PredictionResponse
from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig
from app.services.preprocessing import compose_article_text, preprocess_for_classical_ml


class InferenceError(ValueError):
    pass


class InferenceService:
    def __init__(self, db: Session, artifact_base_dir: Path | None = None) -> None:
        self.repository = TrainingRunRepository(db)
        self.artifact_store = ArtifactStore(artifact_base_dir)

    def predict(self, training_run_id: UUID, request: PredictionRequest) -> PredictionResponse:
        training_run = self.repository.get(training_run_id)
        if training_run is None:
            raise InferenceError("Training run was not found.")
        if training_run.status != TrainingRunStatus.COMPLETED.value or not training_run.artifact_path:
            raise InferenceError("Only completed training runs with artifacts can be used for inference.")

        if training_run.model_family == ModelFamily.TRANSFORMER.value:
            try:
                predicted_label, real_probability, fake_probability, confidence, model_name = (
                    TransformerInferenceService(self.artifact_store.base_dir).predict(training_run, request)
                )
            except (ArtifactError, ValueError, RuntimeError) as exc:
                raise InferenceError(str(exc)) from exc
            return PredictionResponse(
                training_run_id=training_run.id,
                model_family=ModelFamily.TRANSFORMER,
                model_type=ClassicalModelType(training_run.model_type),
                model_name=model_name or training_run.base_model_name,
                predicted_label=predicted_label,
                real_probability=real_probability,
                fake_probability=fake_probability,
                confidence=confidence,
                probability_method=training_run.probability_method,
                message=(
                    "Transformer model-based classification from learned dataset patterns; "
                    "not independent verification of factual truth."
                ),
            )

        try:
            payload, _metadata = self.artifact_store.load(training_run.artifact_path)
        except ArtifactError as exc:
            raise InferenceError(str(exc)) from exc

        composed = compose_article_text(
            title=request.title,
            content=request.content,
            config=TextCompositionConfig(**payload["text_composition_config"]),
        )
        processed = preprocess_for_classical_ml(
            composed,
            PreprocessingConfig(**payload["preprocessing_config"]),
        )
        features = payload["vectorizer"].transform([processed])
        classifier = payload["classifier"]
        predicted_label = str(classifier.predict(features)[0])

        real_probability: float | None = None
        fake_probability: float | None = None
        confidence: float | None = None
        if hasattr(classifier, "predict_proba"):
            probabilities = classifier.predict_proba(features)[0]
            class_to_probability = {
                str(label): round(float(probability), 6)
                for label, probability in zip(classifier.classes_, probabilities, strict=True)
            }
            real_probability = class_to_probability.get(ArticleLabel.REAL.value)
            fake_probability = class_to_probability.get(ArticleLabel.FAKE.value)
            confidence = class_to_probability.get(predicted_label)

        return PredictionResponse(
            training_run_id=training_run.id,
            model_family=ModelFamily.CLASSICAL,
            model_type=ClassicalModelType(training_run.model_type),
            model_name=training_run.base_model_name,
            predicted_label=ArticleLabel(predicted_label),
            real_probability=real_probability,
            fake_probability=fake_probability,
            confidence=confidence,
            probability_method=training_run.probability_method,
            message=(
                "Model-based classification from learned dataset patterns; "
                "not independent verification of factual truth."
            ),
        )
