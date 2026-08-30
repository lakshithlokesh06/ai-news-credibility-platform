from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.explainability.service import ExplanationService
from app.ml.inference import InferenceService
from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, TrainingRunStatus

from tests.test_ml_api import seed_dataset


def train_logistic_model(client: TestClient, tmp_path) -> dict:
    seed_dataset(client, tmp_path)
    response = client.post(
        "/api/v1/ml/training-runs",
        json={
            "model_type": "logistic_regression",
            "text_composition": {"mode": "title_and_content"},
            "tfidf": {"max_features": 500, "ngram_min": 1, "ngram_max": 2},
            "random_seed": 29,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_prediction_persistence_is_optional_and_matches_returned_prediction(
    client: TestClient,
    tmp_path,
) -> None:
    training_run = train_logistic_model(client, tmp_path)
    request_body = {
        "title": "Verified report",
        "content": "confirmed evidence official record committee",
    }

    unsaved = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json=request_body,
    )
    assert unsaved.status_code == 200
    assert unsaved.json()["analysis_id"] is None
    assert client.get("/api/v1/history").json()["total"] == 0

    saved = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={**request_body, "save_to_history": True},
    )
    assert saved.status_code == 200
    prediction = saved.json()
    assert prediction["analysis_id"] is not None

    detail = client.get(f"/api/v1/history/{prediction['analysis_id']}")
    assert detail.status_code == 200
    saved_detail = detail.json()
    assert saved_detail["predicted_label"] == prediction["predicted_label"]
    assert saved_detail["real_probability"] == prediction["real_probability"]
    assert saved_detail["fake_probability"] == prediction["fake_probability"]
    assert saved_detail["confidence"] == prediction["confidence"]
    assert saved_detail["title"] == request_body["title"]
    assert saved_detail["content"] == request_body["content"]


def test_explanation_attaches_to_same_saved_analysis_without_duplicate_history(
    client: TestClient,
    tmp_path,
) -> None:
    training_run = train_logistic_model(client, tmp_path)
    prediction = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
            "save_to_history": True,
        },
    ).json()
    analysis_id = prediction["analysis_id"]

    explanation = client.post(
        f"/api/v1/ml/models/{training_run['id']}/explain",
        json={
            "analysis_id": analysis_id,
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
            "explanation": {"max_items": 4},
        },
    )
    assert explanation.status_code == 200
    explanation_payload = explanation.json()
    assert explanation_payload["analysis_id"] == analysis_id
    assert explanation_payload["real_probability"] == prediction["real_probability"]
    assert explanation_payload["fake_probability"] == prediction["fake_probability"]

    history = client.get("/api/v1/history").json()
    assert history["total"] == 1
    assert history["items"][0]["explanation_available"] is True

    detail = client.get(f"/api/v1/history/{analysis_id}").json()
    assert detail["explanation"]["explanation_method"] == explanation_payload["explanation_method"]
    assert detail["explanation"]["influences_toward_real"] == explanation_payload["influences_toward_real"]
    assert detail["explanation"]["influences_toward_fake"] == explanation_payload["influences_toward_fake"]


def test_explanation_rejects_training_run_and_input_mismatch(client: TestClient, tmp_path) -> None:
    training_run = train_logistic_model(client, tmp_path)
    prediction = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
            "save_to_history": True,
        },
    ).json()

    mismatch_model = client.post(
        f"/api/v1/ml/models/{uuid4()}/explain",
        json={
            "analysis_id": prediction["analysis_id"],
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
        },
    )
    assert mismatch_model.status_code == 400
    assert mismatch_model.json()["detail"]["error_type"] == "training_run_mismatch"

    mismatch_input = client.post(
        f"/api/v1/ml/models/{training_run['id']}/explain",
        json={
            "analysis_id": prediction["analysis_id"],
            "title": "Different headline",
            "content": "confirmed evidence official record committee",
        },
    )
    assert mismatch_input.status_code == 400
    assert mismatch_input.json()["detail"]["error_type"] == "analysis_input_mismatch"


def test_history_list_filters_and_privacy_shape(client: TestClient, tmp_path) -> None:
    training_run = train_logistic_model(client, tmp_path)
    long_content = "confirmed evidence official record committee " * 20
    saved = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={
            "title": "Verified report",
            "content": long_content,
            "save_to_history": True,
        },
    ).json()

    response = client.get("/api/v1/history", params={"predicted_label": saved["predicted_label"]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    item = payload["items"][0]
    assert "content" not in item
    assert item["article_preview"] is not None
    assert len(item["article_preview"]) <= 220

    search = client.get("/api/v1/history", params={"search": "Verified"})
    assert search.status_code == 200
    assert search.json()["total"] == 1

    no_match = client.get("/api/v1/history", params={"model_family": "transformer"})
    assert no_match.status_code == 200
    assert no_match.json()["total"] == 0


def test_history_detail_does_not_rerun_inference_or_explainability(
    client: TestClient,
    tmp_path,
    monkeypatch,
) -> None:
    training_run = train_logistic_model(client, tmp_path)
    prediction = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
            "save_to_history": True,
        },
    ).json()
    client.post(
        f"/api/v1/ml/models/{training_run['id']}/explain",
        json={
            "analysis_id": prediction["analysis_id"],
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
            "explanation": {"max_items": 3},
        },
    )

    def explode(*_args, **_kwargs):
        raise AssertionError("history detail must not recompute inference or SHAP")

    monkeypatch.setattr(InferenceService, "predict", explode)
    monkeypatch.setattr(ExplanationService, "explain", explode)

    detail = client.get(f"/api/v1/history/{prediction['analysis_id']}")
    assert detail.status_code == 200
    assert detail.json()["explanation"] is not None


def test_history_deletion_does_not_affect_training_run(client: TestClient, tmp_path) -> None:
    training_run = train_logistic_model(client, tmp_path)
    prediction = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
            "save_to_history": True,
        },
    ).json()

    deleted = client.delete(f"/api/v1/history/{prediction['analysis_id']}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert client.get(f"/api/v1/history/{prediction['analysis_id']}").status_code == 404
    assert client.get(f"/api/v1/ml/training-runs/{training_run['id']}").status_code == 200


def test_empty_history_statistics(client: TestClient) -> None:
    response = client.get("/api/v1/history/statistics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_saved_analyses"] == 0
    assert payload["likely_real_percentage"] is None
    assert payload["likely_fake_percentage"] is None
    assert payload["average_confidence"] is None
    assert payload["model_family_distribution"] == []


def make_training_run(db_session: Session, *, model_type: ClassicalModelType) -> MLTrainingRun:
    now = datetime.now(UTC)
    run = MLTrainingRun(
        id=uuid4(),
        model_family=(
            ModelFamily.TRANSFORMER.value
            if model_type == ClassicalModelType.DISTILBERT
            else ModelFamily.CLASSICAL.value
        ),
        model_type=model_type.value,
        base_model_name="distilbert-base-uncased" if model_type == ClassicalModelType.DISTILBERT else None,
        model_display_name=f"{model_type.value} run",
        status=TrainingRunStatus.COMPLETED.value,
        preprocessing_config={},
        text_composition_config={"mode": "title_and_content"},
        tfidf_config={},
        transformer_config={},
        model_hyperparameters={},
        split_config={},
        random_seed=1,
        dataset_identifiers=[],
        split_distributions={},
        artifact_path="artifact",
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add(run)
    db_session.commit()
    return run


def add_analysis_record(
    db_session: Session,
    *,
    training_run: MLTrainingRun,
    label: ArticleLabel,
    confidence: float,
    days_ago: int = 0,
    explained: bool = False,
) -> None:
    now = datetime.now(UTC) - timedelta(days=days_ago)
    db_session.add(
        AnalysisRecord(
            id=uuid4(),
            training_run_id=training_run.id,
            model_family=training_run.model_family,
            model_type=training_run.model_type,
            model_name=training_run.base_model_name,
            model_display_name=training_run.model_display_name,
            title=f"{label.value} title",
            content="Saved article body that should never appear in statistics.",
            text_composition_mode="title_and_content",
            predicted_label=label.value,
            real_probability=confidence if label == ArticleLabel.REAL else 1 - confidence,
            fake_probability=confidence if label == ArticleLabel.FAKE else 1 - confidence,
            confidence=confidence,
            probability_method="predict_proba",
            explanation_status=ExplanationStatus.GENERATED if explained else ExplanationStatus.NOT_REQUESTED,
            explanation_method="coefficient_tfidf_local" if explained else None,
            explained_class=label.value if explained else None,
            influences_toward_real=[],
            influences_toward_fake=[],
            explanation_limitations=[],
            explanation_generated_at=now if explained else None,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()


def test_history_statistics_use_real_records_without_article_bodies(
    client: TestClient,
    db_session: Session,
) -> None:
    classical_run = make_training_run(db_session, model_type=ClassicalModelType.LOGISTIC_REGRESSION)
    transformer_run = make_training_run(db_session, model_type=ClassicalModelType.DISTILBERT)
    add_analysis_record(db_session, training_run=classical_run, label=ArticleLabel.REAL, confidence=0.8, days_ago=1)
    add_analysis_record(db_session, training_run=classical_run, label=ArticleLabel.FAKE, confidence=0.6, explained=True)
    add_analysis_record(db_session, training_run=transformer_run, label=ArticleLabel.FAKE, confidence=0.9)

    response = client.get("/api/v1/history/statistics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_saved_analyses"] == 3
    assert payload["likely_real_count"] == 1
    assert payload["likely_fake_count"] == 2
    assert payload["likely_real_percentage"] == pytest.approx(33.33)
    assert payload["likely_fake_percentage"] == pytest.approx(66.67)
    assert payload["average_confidence"] == pytest.approx(0.766667)
    assert payload["average_real_confidence"] == pytest.approx(0.8)
    assert payload["average_fake_confidence"] == pytest.approx(0.75)
    assert payload["analyses_with_explanations"] == 1
    assert payload["analyses_without_explanations"] == 2
    assert {item["name"]: item["count"] for item in payload["model_family_distribution"]} == {
        "classical": 2,
        "transformer": 1,
    }
    assert {item["name"]: item["count"] for item in payload["model_type_distribution"]} == {
        "distilbert": 1,
        "logistic_regression": 2,
    }
    assert len(payload["training_run_distribution"]) == 2
    assert payload["recent_volume"]
    assert "Saved article body" not in response.text
