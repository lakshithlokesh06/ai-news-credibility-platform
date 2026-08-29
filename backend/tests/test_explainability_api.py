from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.explainability.transformer import TransformerExplainer
from app.ml.inference import InferenceService
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, TrainingRunStatus
from app.schemas.ml import ExplanationResponse, PredictionResponse

from tests.test_ml_api import seed_dataset


def test_successful_classical_explanation_api(client: TestClient, tmp_path) -> None:
    seed_dataset(client, tmp_path)
    training_response = client.post(
        "/api/v1/ml/training-runs",
        json={
            "model_type": "logistic_regression",
            "text_composition": {"mode": "title_and_content"},
            "tfidf": {"max_features": 500, "ngram_min": 1, "ngram_max": 2},
            "random_seed": 19,
        },
    )
    training_run = training_response.json()

    response = client.post(
        f"/api/v1/ml/models/{training_run['id']}/explain",
        json={
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
            "explanation": {"max_items": 4},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["training_run_id"] == training_run["id"]
    assert payload["model_family"] == "classical"
    assert payload["explanation_method"] == "coefficient_tfidf_local"
    assert len(payload["influences_toward_real"]) <= 4
    assert payload["limitations"]


def test_explain_api_missing_incomplete_invalid_and_missing_artifact(client: TestClient, db_session) -> None:
    missing = client.post(
        f"/api/v1/ml/models/{uuid4()}/explain",
        json={"title": "Headline", "content": "Article"},
    )
    assert missing.status_code == 400
    assert missing.json()["detail"]["error_type"] == "missing_training_run"

    now = datetime.now(UTC)
    incomplete = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.CLASSICAL.value,
        model_type=ClassicalModelType.LOGISTIC_REGRESSION.value,
        base_model_name=None,
        model_display_name="Incomplete",
        status=TrainingRunStatus.TRAINING.value,
        preprocessing_config={},
        text_composition_config={},
        tfidf_config={},
        transformer_config={},
        model_hyperparameters={},
        split_config={},
        random_seed=1,
        dataset_identifiers=[],
        split_distributions={},
        started_at=now,
        created_at=now,
    )
    missing_artifact = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.CLASSICAL.value,
        model_type=ClassicalModelType.LOGISTIC_REGRESSION.value,
        base_model_name=None,
        model_display_name="Missing artifact",
        status=TrainingRunStatus.COMPLETED.value,
        preprocessing_config={},
        text_composition_config={},
        tfidf_config={},
        transformer_config={},
        model_hyperparameters={},
        split_config={},
        random_seed=1,
        dataset_identifiers=[],
        split_distributions={},
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    unsupported = MLTrainingRun(
        id=uuid4(),
        model_family="unknown",
        model_type="unknown",
        base_model_name=None,
        model_display_name="Unsupported",
        status=TrainingRunStatus.COMPLETED.value,
        preprocessing_config={},
        text_composition_config={},
        tfidf_config={},
        transformer_config={},
        model_hyperparameters={},
        split_config={},
        random_seed=1,
        dataset_identifiers=[],
        split_distributions={},
        artifact_path="unsupported",
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add_all([incomplete, missing_artifact, unsupported])
    db_session.commit()

    invalid_limit = client.post(
        f"/api/v1/ml/models/{missing_artifact.id}/explain",
        json={"title": "Headline", "content": "Article", "explanation": {"max_items": 100}},
    )
    assert invalid_limit.status_code == 422

    incomplete_response = client.post(
        f"/api/v1/ml/models/{incomplete.id}/explain",
        json={"title": "Headline", "content": "Article"},
    )
    assert incomplete_response.status_code == 400
    assert incomplete_response.json()["detail"]["error_type"] == "incomplete_training_run"

    missing_artifact_response = client.post(
        f"/api/v1/ml/models/{missing_artifact.id}/explain",
        json={"title": "Headline", "content": "Article"},
    )
    assert missing_artifact_response.status_code == 400
    assert missing_artifact_response.json()["detail"]["error_type"] == "missing_artifact"

    unsupported_response = client.post(
        f"/api/v1/ml/models/{unsupported.id}/explain",
        json={"title": "Headline", "content": "Article"},
    )
    assert unsupported_response.status_code == 400
    assert unsupported_response.json()["detail"]["error_type"] == "unsupported_model_type"


def test_prediction_api_does_not_invoke_explainability(client: TestClient, tmp_path, monkeypatch) -> None:
    seed_dataset(client, tmp_path)
    training_run = client.post(
        "/api/v1/ml/training-runs",
        json={"model_type": "logistic_regression"},
    ).json()

    def explode(*_args, **_kwargs):
        raise AssertionError("predict endpoint should not compute explanations")

    monkeypatch.setattr("app.explainability.shap_integration.ensure_shap_available", explode)

    response = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={"title": "Verified report", "content": "confirmed official evidence"},
    )

    assert response.status_code == 200
    assert "influences_toward_real" not in response.json()


def test_transformer_explanation_api_dispatches_without_download(client: TestClient, db_session, monkeypatch) -> None:
    now = datetime.now(UTC)
    training_run = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.TRANSFORMER.value,
        model_type=ClassicalModelType.DISTILBERT.value,
        base_model_name="distilbert-base-uncased",
        model_display_name="Transformer explain API",
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
            real_probability=0.1,
            fake_probability=0.9,
            confidence=0.9,
            probability_method="softmax_logits",
            message="mocked",
        )

    def fake_explain(self, run, request, prediction):
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
            limitations=["mocked"],
            message="mocked explanation",
        )

    monkeypatch.setattr(InferenceService, "predict", fake_predict)
    monkeypatch.setattr(TransformerExplainer, "explain", fake_explain)

    response = client.post(
        f"/api/v1/ml/models/{training_run.id}/explain",
        json={
            "title": "Headline",
            "content": "Article",
            "explanation": {"max_transformer_length": 32, "max_evaluations": 4},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_family"] == "transformer"
    assert payload["explanation_method"] == "shap_text"
    assert payload["fake_probability"] == 0.9
