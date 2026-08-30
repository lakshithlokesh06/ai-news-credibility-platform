from collections import Counter
from datetime import UTC, datetime
from statistics import mean, median
from typing import Any

from sqlalchemy.orm import Session

from app.ml.artifacts import ArtifactError, ArtifactStore
from app.ml.dataset import TrainingDatasetBuilder
from app.ml.transformer_dataset import TransformerDatasetBuilder
from app.models.article import NewsArticle
from app.models.training import MLTrainingRun, ModelFamily
from app.monitoring.config import PROFILE_VERSION, TEXT_LENGTH_BINS, TITLE_LENGTH_BINS, MonitoringError
from app.monitoring.drift_metrics import histogram
from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig


def build_reference_profile(
    db: Session,
    training_run: MLTrainingRun,
    *,
    artifact_base_dir=None,
) -> dict[str, Any]:
    if training_run.model_family == ModelFamily.TRANSFORMER.value:
        samples = TransformerDatasetBuilder(db).build(
            dataset_names=training_run.dataset_identifiers or None,
            composition_config=TextCompositionConfig(**training_run.text_composition_config),
            minimum_samples_per_class=1,
        )
        feature_metadata = {
            "method": "model_independent_text_statistics",
            "transformer_max_sequence_length": (training_run.transformer_config or {}).get("max_sequence_length"),
        }
    else:
        samples = TrainingDatasetBuilder(db).build(
            dataset_names=training_run.dataset_identifiers or None,
            composition_config=TextCompositionConfig(**training_run.text_composition_config),
            preprocessing_config=PreprocessingConfig(**training_run.preprocessing_config),
            minimum_samples_per_class=1,
        )
        feature_metadata = _classical_feature_metadata(training_run, artifact_base_dir)

    text_lengths = [len(sample.text) for sample in samples]
    title_lengths = _title_lengths(db, training_run.dataset_identifiers or None)
    label_counts = Counter(sample.label for sample in samples)
    now = datetime.now(UTC)
    return {
        "profile_version": PROFILE_VERSION,
        "sample_count": len(samples),
        "reference_statistics": {
            "created_at": now.isoformat(),
            "model_family": training_run.model_family,
            "model_type": training_run.model_type,
            "text_composition_mode": (training_run.text_composition_config or {}).get("mode"),
            "text_length": _stats(text_lengths),
            "title_length": _stats(title_lengths),
            "text_length_bins": TEXT_LENGTH_BINS,
            "text_length_distribution": histogram([float(value) for value in text_lengths], TEXT_LENGTH_BINS),
            "title_length_bins": TITLE_LENGTH_BINS,
            "title_length_distribution": histogram([float(value) for value in title_lengths], TITLE_LENGTH_BINS),
            "reference_text_lengths": text_lengths[:1000],
        },
        "reference_label_distribution": {
            "REAL": int(label_counts.get("REAL", 0)),
            "FAKE": int(label_counts.get("FAKE", 0)),
        },
        "feature_metadata": feature_metadata,
    }


def _stats(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"average": None, "median": None, "minimum": None, "maximum": None}
    return {
        "average": round(float(mean(values)), 6),
        "median": round(float(median(values)), 6),
        "minimum": min(values),
        "maximum": max(values),
    }


def _title_lengths(db: Session, dataset_names: list[str] | None) -> list[int]:
    from sqlalchemy import select

    statement = select(NewsArticle.title)
    if dataset_names:
        statement = statement.where(NewsArticle.dataset_name.in_(dataset_names))
    return [len(title or "") for title in db.execute(statement).scalars().all()]


def _classical_feature_metadata(training_run: MLTrainingRun, artifact_base_dir) -> dict[str, Any]:
    if not training_run.artifact_path:
        return {"method": "tfidf_artifact_unavailable"}
    try:
        payload, _metadata = ArtifactStore(artifact_base_dir).load(training_run.artifact_path)
    except ArtifactError as exc:
        raise MonitoringError(str(exc), "missing_or_invalid_artifact") from exc
    vectorizer = payload["vectorizer"]
    vocabulary_size = len(getattr(vectorizer, "vocabulary_", {}) or {})
    return {
        "method": "tfidf_vectorizer_reference",
        "vocabulary_size": vocabulary_size,
        "max_features": getattr(vectorizer, "max_features", None),
        "ngram_range": list(getattr(vectorizer, "ngram_range", [])),
    }
