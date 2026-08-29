from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.explainability.phrase_aggregation import aggregate_transformer_tokens
from app.explainability.service import ExplanationService
from app.explainability.shap_integration import compute_linear_shap_values
from app.explainability.transformer import TransformerExplainer
from app.ml.inference import InferenceService
from app.ml.training_service import TrainingService
from app.models.article import ArticleLabel, NewsArticle
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, TrainingRunStatus
from app.schemas.ml import (
    ExplanationConfig,
    ExplanationRequest,
    ExplanationResponse,
    ModelHyperparameters,
    PredictionRequest,
    PredictionResponse,
    TfidfConfig,
    TrainingRunCreate,
)
from app.schemas.preprocessing import TextCompositionConfig


def add_explainability_articles(db_session: Session, samples_per_class: int = 12) -> None:
    now = datetime.now(UTC)
    for index in range(samples_per_class):
        db_session.add(
            NewsArticle(
                title=f"Verified public report {index}",
                content=f"confirmed evidence official statement budget committee verified record {index}",
                label=ArticleLabel.REAL.value,
                source_name="Synthetic source",
                dataset_name="explainability-fixture",
                duplicate_key=f"real-{index}",
                created_at=now,
                updated_at=now,
            )
        )
        db_session.add(
            NewsArticle(
                title=f"Viral fabricated rumor {index}",
                content=f"fabricated hoax conspiracy invented shocking rumor claim {index}",
                label=ArticleLabel.FAKE.value,
                source_name="Synthetic source",
                dataset_name="explainability-fixture",
                duplicate_key=f"fake-{index}",
                created_at=now,
                updated_at=now,
            )
        )
    db_session.commit()


def explanation_training_config(model_type: ClassicalModelType) -> TrainingRunCreate:
    return TrainingRunCreate(
        model_type=model_type,
        text_composition=TextCompositionConfig(mode="title_and_content"),
        tfidf=TfidfConfig(max_features=500, ngram_min=1, ngram_max=2),
        hyperparameters=ModelHyperparameters(calibration_cv=2, max_iter=2000),
        random_seed=7,
    )


def test_logistic_regression_explanation_maps_tfidf_features_to_real_and_fake(
    db_session: Session,
    tmp_path: Path,
) -> None:
    add_explainability_articles(db_session)
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        explanation_training_config(ClassicalModelType.LOGISTIC_REGRESSION)
    )

    explanation = ExplanationService(db_session, artifact_base_dir=tmp_path).explain(
        training_run.id,
        ExplanationRequest(
            title="Verified official report",
            content="confirmed evidence official record committee",
            explanation=ExplanationConfig(max_items=5),
        ),
    )

    assert explanation.predicted_label in {ArticleLabel.REAL, ArticleLabel.FAKE}
    assert explanation.real_probability is not None
    assert explanation.fake_probability is not None
    assert pytest.approx(explanation.real_probability + explanation.fake_probability, abs=0.00001) == 1.0
    assert explanation.explanation_method == "coefficient_tfidf_local"
    assert all(item.direction == ArticleLabel.REAL for item in explanation.influences_toward_real)
    assert all(item.direction == ArticleLabel.FAKE for item in explanation.influences_toward_fake)
    assert [item.rank for item in explanation.influences_toward_real] == list(
        range(1, len(explanation.influences_toward_real) + 1)
    )
    assert any("official" in item.text or "verified" in item.text for item in explanation.influences_toward_real)


def test_classical_ngram_features_and_empty_no_feature_case(db_session: Session, tmp_path: Path) -> None:
    add_explainability_articles(db_session)
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        explanation_training_config(ClassicalModelType.LOGISTIC_REGRESSION)
    )

    ngram_explanation = ExplanationService(db_session, artifact_base_dir=tmp_path).explain(
        training_run.id,
        ExplanationRequest(
            title="Viral fabricated rumor",
            content="fabricated hoax shocking rumor claim",
            explanation=ExplanationConfig(max_items=8),
        ),
    )
    all_features = ngram_explanation.influences_toward_fake + ngram_explanation.influences_toward_real
    assert any(" " in item.text for item in all_features)

    empty_explanation = ExplanationService(db_session, artifact_base_dir=tmp_path).explain(
        training_run.id,
        ExplanationRequest(
            title="unseenwordalpha",
            content="unseenwordbeta",
            explanation=ExplanationConfig(max_items=5),
        ),
    )
    assert empty_explanation.influences_toward_real == []
    assert empty_explanation.influences_toward_fake == []


def test_linear_svm_explanation_uses_underlying_decision_function(
    db_session: Session,
    tmp_path: Path,
) -> None:
    add_explainability_articles(db_session)
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        explanation_training_config(ClassicalModelType.LINEAR_SVM)
    )

    explanation = ExplanationService(db_session, artifact_base_dir=tmp_path).explain(
        training_run.id,
        ExplanationRequest(
            title="Viral fabricated rumor",
            content="fabricated hoax conspiracy invented shocking rumor",
            explanation=ExplanationConfig(max_items=5),
        ),
    )

    assert explanation.explanation_method == "linear_svm_underlying_decision_function"
    assert explanation.influences_toward_fake
    assert any("underlying fitted linear decision function" in limitation for limitation in explanation.limitations)


def test_tiny_shap_linear_integration_is_real_and_fast(db_session: Session, tmp_path: Path) -> None:
    add_explainability_articles(db_session)
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        explanation_training_config(ClassicalModelType.LOGISTIC_REGRESSION)
    )

    explanation = ExplanationService(db_session, artifact_base_dir=tmp_path).explain(
        training_run.id,
        ExplanationRequest(
            title="Verified report",
            content="confirmed official evidence",
            explanation=ExplanationConfig(method="shap", max_items=4),
        ),
    )

    assert explanation.explanation_method == "shap_linear_logistic"
    assert explanation.influences_toward_real or explanation.influences_toward_fake


def test_compute_linear_shap_values_returns_one_value_per_feature() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    vectorizer = TfidfVectorizer()
    features = vectorizer.fit_transform(["real verified", "fake hoax", "real official", "fake rumor"])
    classifier = LogisticRegression().fit(features, ["REAL", "FAKE", "REAL", "FAKE"])

    values = compute_linear_shap_values(classifier, features[:1])

    assert len(values) == features.shape[1]
    assert any(abs(value) > 0 for value in values)


def test_transformer_subword_aggregation_preserves_offsets_and_direction() -> None:
    items = aggregate_transformer_tokens(
        tokens=["[CLS]", "mis", "##info", "credible"],
        real_scores=[0.0, -0.1, -0.2, 0.4],
        fake_scores=[0.0, 0.1, 0.2, -0.4],
        offsets=[(0, 0), (0, 3), (3, 7), (8, 16)],
    )

    assert items[0].text == "misinfo"
    assert items[0].score_for_fake == pytest.approx(0.3)
    assert items[0].start_offset == 0
    assert items[0].end_offset == 7
    assert items[0].source_tokens == ("mis", "##info")
    assert items[1].text == "credible"


def test_explanation_config_bounds() -> None:
    with pytest.raises(ValidationError):
        ExplanationConfig(max_items=100)
    with pytest.raises(ValidationError):
        ExplanationConfig(max_transformer_length=1024)
    with pytest.raises(ValidationError):
        ExplanationConfig(max_evaluations=1)


def test_transformer_explanation_dispatch_is_mockable_and_preserves_prediction(
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    now = datetime.now(UTC)
    training_run = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.TRANSFORMER.value,
        model_type=ClassicalModelType.DISTILBERT.value,
        base_model_name="distilbert-base-uncased",
        model_display_name="Transformer explainable",
        status=TrainingRunStatus.COMPLETED.value,
        preprocessing_config={},
        text_composition_config={"mode": "title_and_content", "separator": "\n\n"},
        tfidf_config={},
        transformer_config={"max_sequence_length": 32},
        model_hyperparameters={},
        split_config={},
        random_seed=42,
        dataset_identifiers=[],
        split_distributions={},
        artifact_path="transformer-artifact",
        artifact_checksum="checksum",
        artifact_version="transformer-ml-v1",
        probability_method="softmax_logits",
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add(training_run)
    db_session.commit()

    def fake_predict(self, training_run_id, request):
        return PredictionResponse(
            training_run_id=training_run_id,
            model_family=ModelFamily.TRANSFORMER,
            model_type=ClassicalModelType.DISTILBERT,
            model_name="distilbert-base-uncased",
            predicted_label=ArticleLabel.FAKE,
            real_probability=0.25,
            fake_probability=0.75,
            confidence=0.75,
            probability_method="softmax_logits",
            message="mocked",
        )

    def fake_explain(self, run, request, prediction):
        assert run.id == training_run.id
        assert request.explanation.max_transformer_length == 32
        return ExplanationResponse(
            training_run_id=run.id,
            model_family=ModelFamily.TRANSFORMER,
            model_type=ClassicalModelType.DISTILBERT,
            model_name=prediction.model_name,
            predicted_label=prediction.predicted_label,
            real_probability=prediction.real_probability,
            fake_probability=prediction.fake_probability,
            confidence=prediction.confidence,
            probability_method=prediction.probability_method,
            explanation_method="shap_text",
            explained_class=prediction.predicted_label,
            influences_toward_real=[],
            influences_toward_fake=[],
            limitations=["mocked transformer shap"],
            message="mocked explanation",
        )

    monkeypatch.setattr(InferenceService, "predict", fake_predict)
    monkeypatch.setattr(TransformerExplainer, "explain", fake_explain)

    response = ExplanationService(db_session, artifact_base_dir=tmp_path).explain(
        training_run.id,
        ExplanationRequest(
            title="Headline",
            content="Article",
            explanation=ExplanationConfig(max_transformer_length=32),
        ),
    )

    assert response.explanation_method == "shap_text"
    assert response.predicted_label == ArticleLabel.FAKE
    assert response.fake_probability == 0.75
