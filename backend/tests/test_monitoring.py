from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.explainability.service import ExplanationService
from app.ml.inference import InferenceService
from app.ml.training_service import TrainingService
from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel, NewsArticle
from app.models.monitoring import ModelMonitoringProfile
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, TrainingRunStatus
from app.monitoring.config import PROFILE_VERSION
from app.monitoring.drift_metrics import classify_metric, jensen_shannon_divergence, ks_statistic, population_stability_index
from app.monitoring.service import MonitoringService
from app.schemas.ml import ModelHyperparameters, TfidfConfig, TrainingRunCreate
from app.schemas.preprocessing import TextCompositionConfig


def add_monitoring_articles(db_session: Session, samples_per_class: int = 12) -> None:
    now = datetime.now(UTC)
    for index in range(samples_per_class):
        db_session.add(
            NewsArticle(
                title=f"Verified report {index}",
                content=f"confirmed official evidence record committee {index}",
                label=ArticleLabel.REAL.value,
                dataset_name="monitoring-fixture",
                duplicate_key=f"real-monitor-{index}",
                created_at=now,
                updated_at=now,
            )
        )
        db_session.add(
            NewsArticle(
                title=f"Viral hoax {index}",
                content=f"fabricated rumor conspiracy invented claim {index}",
                label=ArticleLabel.FAKE.value,
                dataset_name="monitoring-fixture",
                duplicate_key=f"fake-monitor-{index}",
                created_at=now,
                updated_at=now,
            )
        )
    db_session.commit()


def monitoring_training_config(model_type: ClassicalModelType = ClassicalModelType.LOGISTIC_REGRESSION) -> TrainingRunCreate:
    return TrainingRunCreate(
        model_type=model_type,
        text_composition=TextCompositionConfig(mode="title_and_content"),
        tfidf=TfidfConfig(max_features=500, ngram_min=1, ngram_max=2),
        hyperparameters=ModelHyperparameters(calibration_cv=2, max_iter=2000),
        random_seed=37,
    )


def train_monitoring_model(db_session: Session, tmp_path: Path) -> MLTrainingRun:
    add_monitoring_articles(db_session)
    return TrainingService(db_session, artifact_base_dir=tmp_path).train(monitoring_training_config())


def add_analysis(
    db_session: Session,
    training_run: MLTrainingRun,
    *,
    label: ArticleLabel,
    confidence: float,
    title: str = "Verified report",
    content: str = "confirmed official evidence",
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
            title=title,
            content=content,
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


def test_drift_metrics_are_stable_shifted_and_numerically_safe() -> None:
    assert population_stability_index([10, 10], [10, 10]) == pytest.approx(0.0)
    assert jensen_shannon_divergence([10, 10], [10, 10]) == pytest.approx(0.0)
    assert ks_statistic([1, 2, 3], [1, 2, 3]) == pytest.approx(0.0)

    assert population_stability_index([20, 1], [1, 20]) > 1.0
    assert jensen_shannon_divergence([20, 1], [1, 20]) > 0.4
    assert ks_statistic([1, 2, 3], [100, 200, 300]) == pytest.approx(1.0)
    assert population_stability_index([0, 10], [5, 5]) is not None
    assert classify_metric(0.01, 0.1, 0.25) == "stable"
    assert classify_metric(0.12, 0.1, 0.25) == "warning"
    assert classify_metric(0.3, 0.1, 0.25) == "drift_detected"
    assert classify_metric(None, 0.1, 0.25) == "insufficient_data"


def test_reference_profile_generation_and_refresh(db_session: Session, tmp_path: Path) -> None:
    training_run = train_monitoring_model(db_session, tmp_path)
    profile = MonitoringService(db_session, artifact_base_dir=tmp_path).generate_reference_profile(training_run.id)

    assert profile.profile_version == PROFILE_VERSION
    assert profile.sample_count == training_run.dataset_article_count
    assert profile.reference_label_distribution == {"REAL": 12, "FAKE": 12}
    assert profile.feature_metadata["method"] == "tfidf_vectorizer_reference"
    assert profile.feature_metadata["vocabulary_size"] > 0

    refreshed = MonitoringService(db_session, artifact_base_dir=tmp_path).generate_reference_profile(training_run.id)
    assert refreshed.id == profile.id


def test_reference_profile_requires_completed_model(db_session: Session, tmp_path: Path) -> None:
    now = datetime.now(UTC)
    run = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.CLASSICAL.value,
        model_type=ClassicalModelType.LOGISTIC_REGRESSION.value,
        model_display_name="Training",
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
    db_session.add(run)
    db_session.commit()

    with pytest.raises(Exception, match="Only completed"):
        MonitoringService(db_session, artifact_base_dir=tmp_path).generate_reference_profile(run.id)
    with pytest.raises(Exception, match="not found"):
        MonitoringService(db_session, artifact_base_dir=tmp_path).generate_reference_profile(uuid4())


def test_transformer_profile_uses_model_independent_statistics(db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    now = datetime.now(UTC)
    run = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.TRANSFORMER.value,
        model_type=ClassicalModelType.DISTILBERT.value,
        base_model_name="distilbert-base-uncased",
        model_display_name="Transformer monitor",
        status=TrainingRunStatus.COMPLETED.value,
        preprocessing_config={},
        text_composition_config={"mode": "title_and_content", "separator": "\n\n"},
        tfidf_config={},
        transformer_config={"max_sequence_length": 64},
        model_hyperparameters={},
        split_config={},
        random_seed=1,
        dataset_identifiers=["monitoring-fixture"],
        split_distributions={},
        artifact_path="not-loaded",
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add(run)
    db_session.commit()

    profile = MonitoringService(db_session, artifact_base_dir=tmp_path).generate_reference_profile(run.id)

    assert profile.feature_metadata["method"] == "model_independent_text_statistics"
    assert profile.feature_metadata["transformer_max_sequence_length"] == 64


def test_monitoring_returns_insufficient_data_without_history(db_session: Session, tmp_path: Path) -> None:
    training_run = train_monitoring_model(db_session, tmp_path)

    monitoring = MonitoringService(db_session, artifact_base_dir=tmp_path).monitor_model(training_run.id)

    assert monitoring.reference_profile_status == "available"
    assert monitoring.overall_status == "insufficient_data"
    assert monitoring.sample_counts["current_window"] == 0
    assert monitoring.prediction_drift.status == "insufficient_data"


def test_monitoring_stable_and_shifted_synthetic_history(db_session: Session, tmp_path: Path) -> None:
    training_run = train_monitoring_model(db_session, tmp_path)
    service = MonitoringService(db_session, artifact_base_dir=tmp_path)
    service.generate_reference_profile(training_run.id)
    for index in range(5):
        add_analysis(
            db_session,
            training_run,
            label=ArticleLabel.REAL,
            confidence=0.78,
            title=f"Verified report {index}",
            content=f"confirmed official evidence record committee {index}",
            days_ago=index,
        )
        add_analysis(
            db_session,
            training_run,
            label=ArticleLabel.FAKE,
            confidence=0.82,
            title=f"Viral hoax {index}",
            content=f"fabricated rumor conspiracy invented claim {index}",
            days_ago=index,
        )

    stable = service.monitor_model(training_run.id)
    assert stable.overall_status in {"healthy", "watch"}
    assert stable.prediction_drift.status == "stable"
    assert stable.usage_metrics.total_analyses == 10
    assert stable.usage_metrics.real_prediction_count == 5
    assert stable.usage_metrics.fake_prediction_count == 5

    for index in range(30):
        add_analysis(
            db_session,
            training_run,
            label=ArticleLabel.FAKE,
            confidence=0.55,
            title="Extreme mismatch headline " * 20,
            content="very long shifted input " * 300,
            days_ago=index,
        )

    shifted = service.monitor_model(training_run.id)
    assert shifted.overall_status in {"watch", "drift_detected"}
    assert shifted.prediction_drift.status in {"warning", "drift_detected"}
    assert any(metric.status in {"warning", "drift_detected"} for metric in shifted.input_drift_metrics)


def test_monitoring_is_scoped_to_training_run(db_session: Session, tmp_path: Path) -> None:
    first = train_monitoring_model(db_session, tmp_path)
    second = TrainingService(db_session, artifact_base_dir=tmp_path).train(monitoring_training_config())
    for _index in range(10):
        add_analysis(db_session, first, label=ArticleLabel.FAKE, confidence=0.9, content="fabricated rumor")

    first_monitoring = MonitoringService(db_session, artifact_base_dir=tmp_path).monitor_model(first.id)
    second_monitoring = MonitoringService(db_session, artifact_base_dir=tmp_path).monitor_model(second.id)

    assert first_monitoring.sample_counts["current_window"] == 10
    assert second_monitoring.sample_counts["current_window"] == 0


def test_monitoring_does_not_rerun_inference_explainability_or_training(
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    training_run = train_monitoring_model(db_session, tmp_path)
    for _index in range(10):
        add_analysis(db_session, training_run, label=ArticleLabel.REAL, confidence=0.8)

    def explode(*_args, **_kwargs):
        raise AssertionError("monitoring should not run inference, explanations, or training")

    monkeypatch.setattr(InferenceService, "predict", explode)
    monkeypatch.setattr(ExplanationService, "explain", explode)
    monkeypatch.setattr(TrainingService, "train", explode)

    monitoring = MonitoringService(db_session, artifact_base_dir=tmp_path).monitor_model(training_run.id)

    assert monitoring.usage_metrics.total_analyses == 10


def test_monitoring_api_overview_detail_profile_and_privacy(client: TestClient, db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path / "models").train(
        monitoring_training_config()
    )
    for _index in range(10):
        add_analysis(db_session, training_run, label=ArticleLabel.REAL, confidence=0.8, content="private article body")

    overview = client.get("/api/v1/monitoring")
    assert overview.status_code == 200
    assert overview.json()["total_completed_models"] == 1
    assert "private article body" not in overview.text

    detail = client.get(f"/api/v1/monitoring/models/{training_run.id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["training_run_id"] == str(training_run.id)
    assert payload["usage_metrics"]["total_analyses"] == 10
    assert "private article body" not in detail.text

    profile = client.post(f"/api/v1/monitoring/models/{training_run.id}/reference-profile")
    assert profile.status_code == 200
    assert profile.json()["training_run_id"] == str(training_run.id)

    missing = client.get(f"/api/v1/monitoring/models/{uuid4()}")
    assert missing.status_code == 404

    invalid_config = client.get(f"/api/v1/monitoring/models/{training_run.id}", params={"window_size": 1})
    assert invalid_config.status_code == 422
