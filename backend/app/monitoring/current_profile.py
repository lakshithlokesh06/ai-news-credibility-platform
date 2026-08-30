from collections import Counter, defaultdict
from statistics import mean, median

from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel
from app.models.training import ModelFamily
from app.monitoring.config import CONFIDENCE_BINS, TEXT_LENGTH_BINS, TITLE_LENGTH_BINS
from app.monitoring.drift_metrics import histogram
from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig
from app.services.preprocessing import (
    EmptyTextError,
    compose_article_text,
    preprocess_for_classical_ml,
    preprocess_for_transformer,
)


def build_current_profile(
    records: list[AnalysisRecord],
    *,
    model_family: str | None = None,
    composition_config: TextCompositionConfig | None = None,
    preprocessing_config: PreprocessingConfig | None = None,
) -> dict:
    text_lengths = [
        len(_model_input_text(record, model_family, composition_config, preprocessing_config))
        for record in records
    ]
    title_lengths = [len(record.title or "") for record in records]
    confidences = [record.confidence for record in records if record.confidence is not None]
    real_probabilities = [record.real_probability for record in records if record.real_probability is not None]
    fake_probabilities = [record.fake_probability for record in records if record.fake_probability is not None]
    predictions = Counter(record.predicted_label for record in records)
    recent_volume: dict[str, int] = defaultdict(int)
    for record in records:
        recent_volume[record.created_at.date().isoformat()] += 1

    return {
        "sample_count": len(records),
        "text_lengths": text_lengths,
        "text_length_distribution": histogram([float(value) for value in text_lengths], TEXT_LENGTH_BINS),
        "title_lengths": title_lengths,
        "title_length_distribution": histogram([float(value) for value in title_lengths], TITLE_LENGTH_BINS),
        "prediction_distribution": {
            ArticleLabel.REAL.value: int(predictions.get(ArticleLabel.REAL.value, 0)),
            ArticleLabel.FAKE.value: int(predictions.get(ArticleLabel.FAKE.value, 0)),
        },
        "confidence_values": confidences,
        "confidence_distribution": histogram([float(value) for value in confidences], CONFIDENCE_BINS),
        "average_confidence": _average(confidences),
        "median_confidence": _median(confidences),
        "average_real_probability": _average(real_probabilities),
        "average_fake_probability": _average(fake_probabilities),
        "real_prediction_count": int(predictions.get(ArticleLabel.REAL.value, 0)),
        "fake_prediction_count": int(predictions.get(ArticleLabel.FAKE.value, 0)),
        "explanation_count": sum(1 for record in records if record.explanation_status == ExplanationStatus.GENERATED),
        "last_used_at": max((record.created_at for record in records), default=None),
        "recent_volume": [{"date": date, "count": count} for date, count in sorted(recent_volume.items())],
    }


def _model_input_text(
    record: AnalysisRecord,
    model_family: str | None,
    composition_config: TextCompositionConfig | None,
    preprocessing_config: PreprocessingConfig | None,
) -> str:
    try:
        composed = compose_article_text(
            title=record.title,
            content=record.content,
            config=composition_config,
        )
        if model_family == ModelFamily.TRANSFORMER.value:
            return preprocess_for_transformer(composed)
        return preprocess_for_classical_ml(composed, preprocessing_config)
    except EmptyTextError:
        return ""


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(median(values)), 6)
