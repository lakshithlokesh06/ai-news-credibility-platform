from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel
from app.models.review import AnalysisReview
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, TrainingRunStatus


def make_run(db_session: Session, *, display_name: str = "Reviewed model") -> MLTrainingRun:
    now = datetime.now(UTC)
    run = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.CLASSICAL.value,
        model_type=ClassicalModelType.LOGISTIC_REGRESSION.value,
        base_model_name=None,
        model_display_name=display_name,
        status=TrainingRunStatus.COMPLETED.value,
        lifecycle_status=None,
        preprocessing_config={},
        text_composition_config={"mode": "title_and_content"},
        tfidf_config={},
        transformer_config={},
        model_hyperparameters={},
        split_config={},
        random_seed=7,
        train_count=10,
        validation_count=4,
        test_count=4,
        dataset_article_count=18,
        dataset_identifiers=["synthetic"],
        split_distributions={},
        validation_metrics={"accuracy": 0.75, "precision": 0.8, "recall": 0.8, "f1": 0.8, "roc_auc": 0.9},
        test_metrics={"accuracy": 0.7, "precision": 0.75, "recall": 0.6, "f1": 0.666667, "roc_auc": 0.8},
        artifact_path="artifact",
        artifact_checksum="abc",
        artifact_version="1",
        probability_method="predict_proba",
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add(run)
    db_session.commit()
    return run


def add_reviewed_analysis(
    db_session: Session,
    *,
    run: MLTrainingRun,
    predicted: ArticleLabel,
    verified: ArticleLabel | None = None,
    confidence: float = 0.8,
    fake_probability: float | None = None,
    days_ago: int = 0,
    explained: bool = False,
) -> AnalysisRecord:
    now = datetime.now(UTC) - timedelta(days=days_ago)
    record = AnalysisRecord(
        id=uuid4(),
        training_run_id=run.id,
        model_family=run.model_family,
        model_type=run.model_type,
        model_name=run.base_model_name,
        model_display_name=run.model_display_name,
        title=f"{predicted.value} analysis",
        content="Private preview sentence. " + ("x" * 260) + " SECRET_FULL_BODY_SUFFIX",
        text_composition_mode="title_and_content",
        predicted_label=predicted.value,
        real_probability=(1 - fake_probability) if fake_probability is not None else (
            confidence if predicted == ArticleLabel.REAL else 1 - confidence
        ),
        fake_probability=fake_probability if fake_probability is not None else (
            confidence if predicted == ArticleLabel.FAKE else 1 - confidence
        ),
        confidence=confidence,
        probability_method="predict_proba",
        explanation_status=ExplanationStatus.GENERATED if explained else ExplanationStatus.NOT_REQUESTED,
        explanation_method="coefficient_tfidf_local" if explained else None,
        explained_class=predicted.value if explained else None,
        influences_toward_real=[],
        influences_toward_fake=[],
        explanation_limitations=[],
        explanation_generated_at=now if explained else None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(record)
    db_session.flush()
    if verified is not None:
        db_session.add(
            AnalysisReview(
                id=uuid4(),
                analysis_id=record.id,
                verified_label=verified.value,
                status="reviewed",
                reviewer_note="checked by editor",
                evidence_note="source material reviewed",
                created_at=now,
                updated_at=now,
            )
        )
    db_session.commit()
    db_session.refresh(record)
    return record


def seed_metric_fixture(db_session: Session) -> tuple[MLTrainingRun, list[AnalysisRecord]]:
    run = make_run(db_session)
    records = [
        add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.FAKE, verified=ArticleLabel.FAKE, confidence=0.9, fake_probability=0.9),
        add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.FAKE, verified=ArticleLabel.REAL, confidence=0.8, fake_probability=0.8, explained=True),
        add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.REAL, verified=ArticleLabel.FAKE, confidence=0.7, fake_probability=0.3),
        add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.REAL, verified=ArticleLabel.REAL, confidence=0.6, fake_probability=0.4),
    ]
    return run, records


def test_review_create_update_and_one_current_review(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.FAKE)

    created = client.put(
        f"/api/v1/history/{analysis.id}/review",
        json={"verified_label": "REAL", "reviewer_note": "  concise note  ", "evidence_note": " reference note "},
    )
    assert created.status_code == 200
    assert created.json()["review"]["verified_label"] == "REAL"
    assert created.json()["review"]["is_prediction_correct"] is False

    updated = client.put(f"/api/v1/history/{analysis.id}/review", json={"verified_label": "FAKE"})
    assert updated.status_code == 200
    assert updated.json()["review"]["verified_label"] == "FAKE"
    assert updated.json()["review"]["is_prediction_correct"] is True
    reviews = db_session.execute(select(AnalysisReview).where(AnalysisReview.analysis_id == analysis.id)).scalars().all()
    assert len(reviews) == 1


def test_review_validation_and_unknown_analysis(client: TestClient) -> None:
    missing = client.put(f"/api/v1/history/{uuid4()}/review", json={"verified_label": "REAL"})
    assert missing.status_code == 404
    assert missing.json()["detail"]["error_type"] == "analysis_not_found"

    invalid = client.put(f"/api/v1/history/{uuid4()}/review", json={"verified_label": "MOSTLY_TRUE"})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"

    too_long = client.put(
        f"/api/v1/history/{uuid4()}/review",
        json={"verified_label": "REAL", "reviewer_note": "x" * 1001},
    )
    assert too_long.status_code == 422


def test_review_delete_and_analysis_delete_cleanup(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.REAL, verified=ArticleLabel.REAL)

    deleted = client.delete(f"/api/v1/history/{analysis.id}/review")
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/history/{analysis.id}").json()["review"]["status"] == "unreviewed"

    client.put(f"/api/v1/history/{analysis.id}/review", json={"verified_label": "REAL"})
    assert client.delete(f"/api/v1/history/{analysis.id}").status_code == 200
    assert db_session.execute(select(AnalysisReview).where(AnalysisReview.analysis_id == analysis.id)).scalars().all() == []


def test_history_review_filters_and_privacy(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    reviewed = add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.FAKE, verified=ArticleLabel.REAL)
    unreviewed = add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.REAL)

    reviewed_response = client.get("/api/v1/history", params={"review_filter": "reviewed"})
    assert reviewed_response.status_code == 200
    assert reviewed_response.json()["total"] == 1
    assert reviewed_response.json()["items"][0]["id"] == str(reviewed.id)
    assert "SECRET_FULL_BODY_SUFFIX" not in reviewed_response.text

    unreviewed_response = client.get("/api/v1/history", params={"review_filter": "unreviewed"})
    assert unreviewed_response.json()["total"] == 1
    assert unreviewed_response.json()["items"][0]["id"] == str(unreviewed.id)

    incorrect_response = client.get("/api/v1/history", params={"review_filter": "incorrect"})
    assert incorrect_response.json()["total"] == 1
    assert incorrect_response.json()["items"][0]["review"]["is_prediction_correct"] is False


def test_review_statistics_api(client: TestClient, db_session: Session) -> None:
    run, _records = seed_metric_fixture(db_session)
    add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.REAL)

    response = client.get("/api/v1/reviews/statistics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_analyses"] == 5
    assert payload["reviewed_analyses"] == 4
    assert payload["unreviewed_analyses"] == 1
    assert payload["review_coverage_percentage"] == pytest.approx(80.0)
    assert payload["reviewed_real_count"] == 2
    assert payload["reviewed_fake_count"] == 2
    assert payload["correct_prediction_count"] == 2
    assert payload["incorrect_prediction_count"] == 2
    assert payload["per_training_run"][0]["training_run_id"] == str(run.id)


def test_performance_metrics_and_roc_auc(client: TestClient, db_session: Session) -> None:
    run, _records = seed_metric_fixture(db_session)

    response = client.get("/api/v1/reviews/performance", params={"training_run_id": str(run.id)})
    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "training_run"
    assert payload["reviewed_count"] == 4
    assert payload["correct_count"] == 2
    assert payload["accuracy"] == pytest.approx(0.5)
    assert payload["precision"] == pytest.approx(0.5)
    assert payload["recall"] == pytest.approx(0.5)
    assert payload["f1"] == pytest.approx(0.5)
    assert payload["roc_auc"]["available"] is True
    assert payload["roc_auc"]["value"] == pytest.approx(0.5)
    assert payload["confusion_matrix"]["matrix"] == [[1, 1], [1, 1]]
    assert payload["confusion_matrix"]["positive_class"] == "FAKE"
    assert payload["sufficiency_status"] == "preliminary"
    assert payload["held_out_test_metrics"]["f1"] == pytest.approx(0.666667)


def test_performance_edges_and_model_scoping(client: TestClient, db_session: Session) -> None:
    run_one = make_run(db_session, display_name="One")
    run_two = make_run(db_session, display_name="Two")
    add_reviewed_analysis(db_session, run=run_one, predicted=ArticleLabel.FAKE, verified=ArticleLabel.FAKE)
    add_reviewed_analysis(db_session, run=run_two, predicted=ArticleLabel.REAL, verified=ArticleLabel.REAL)

    scoped = client.get("/api/v1/reviews/performance", params={"training_run_id": str(run_one.id)}).json()
    assert scoped["reviewed_count"] == 1
    assert scoped["correct_count"] == 1
    assert scoped["roc_auc"]["available"] is False
    assert "both REAL and FAKE" in scoped["roc_auc"]["reason"]

    empty = client.get("/api/v1/reviews/performance", params={"training_run_id": str(uuid4())})
    assert empty.status_code == 404


def test_calibration_metrics_and_bins(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.FAKE, verified=ArticleLabel.FAKE, confidence=0.9, fake_probability=0.9)
    add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.REAL, verified=ArticleLabel.REAL, confidence=0.8, fake_probability=0.2)
    add_reviewed_analysis(db_session, run=run, predicted=ArticleLabel.FAKE, verified=ArticleLabel.REAL, confidence=0.7, fake_probability=0.7)

    response = client.get("/api/v1/reviews/calibration", params={"training_run_id": str(run.id), "bins": "5"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 3
    assert payload["brier_score"] == pytest.approx((0.01 + 0.04 + 0.49) / 3)
    assert payload["expected_calibration_error"] == pytest.approx(0.333333)
    assert [item["sample_count"] for item in payload["reliability_bins"]] == [1, 2]

    invalid_bins = client.get("/api/v1/reviews/calibration", params={"bins": "1"})
    assert invalid_bins.status_code == 422


def test_empty_calibration_and_zero_reviews(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    response = client.get("/api/v1/reviews/calibration", params={"training_run_id": str(run.id)})
    assert response.status_code == 200
    assert response.json()["sufficiency_status"] == "insufficient_data"
    assert response.json()["reliability_bins"] == []

    performance = client.get("/api/v1/reviews/performance", params={"training_run_id": str(run.id)})
    assert performance.json()["reviewed_count"] == 0
    assert performance.json()["accuracy"] is None


def test_error_analysis_classification_filtering_and_privacy(client: TestClient, db_session: Session) -> None:
    run, records = seed_metric_fixture(db_session)

    false_positive = client.get(
        "/api/v1/reviews/errors",
        params={"training_run_id": str(run.id), "error_type": "false_positive"},
    )
    assert false_positive.status_code == 200
    payload = false_positive.json()
    assert payload["total"] == 1
    assert payload["items"][0]["analysis_id"] == str(records[1].id)
    assert payload["items"][0]["error_type"] == "false_positive"
    assert payload["items"][0]["explanation_available"] is True
    assert "SECRET_FULL_BODY_SUFFIX" not in false_positive.text

    high_confidence = client.get(
        "/api/v1/reviews/errors",
        params={"training_run_id": str(run.id), "min_confidence": "0.8"},
    ).json()
    assert high_confidence["total"] == 2
    assert high_confidence["statistics"]["average_confidence_correct"] == pytest.approx(0.75)
    assert high_confidence["statistics"]["average_confidence_incorrect"] == pytest.approx(0.75)
    assert "Model predicted FAKE" in high_confidence["definitions"]["false_positive"]
