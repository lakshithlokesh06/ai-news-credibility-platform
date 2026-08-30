from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.training import ClassicalModelType, ModelLifecycleStatus, TrainingRunStatus
from app.schemas.ml import ModelHyperparameters, TfidfConfig, TrainingRunCreate
from app.schemas.preprocessing import TextCompositionConfig
from app.services.experiments import ExperimentError, ExperimentService
from app.ml.training_service import TrainingService
from tests.test_monitoring import add_monitoring_articles


def experiment_training_config(
    *,
    name: str,
    model_type: ClassicalModelType = ClassicalModelType.LOGISTIC_REGRESSION,
    text_mode: str = "title_and_content",
    dataset_names: list[str] | None = None,
) -> TrainingRunCreate:
    return TrainingRunCreate(
        model_type=model_type,
        model_display_name=name,
        description=f"{name} description",
        tags=["baseline", "Prompt 8"],
        dataset_names=dataset_names,
        text_composition=TextCompositionConfig(mode=text_mode),
        tfidf=TfidfConfig(max_features=500, ngram_min=1, ngram_max=2),
        hyperparameters=ModelHyperparameters(calibration_cv=2, max_iter=2000),
        random_seed=37,
    )


def train_experiment(db_session: Session, tmp_path: Path, *, name: str, text_mode: str = "title_and_content"):
    return TrainingService(db_session, artifact_base_dir=tmp_path).train(
        experiment_training_config(name=name, text_mode=text_mode)
    )


def test_completed_training_runs_become_candidates(db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    run = train_experiment(db_session, tmp_path, name="Candidate model")

    assert run.status == TrainingRunStatus.COMPLETED.value
    assert run.lifecycle_status == ModelLifecycleStatus.CANDIDATE.value
    assert run.description == "Candidate model description"
    assert run.tags == ["baseline", "Prompt 8"]
    assert run.environment_versions["python"]


def test_champion_promotion_demotes_existing_champion_and_records_events(db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    first = train_experiment(db_session, tmp_path, name="First candidate")
    second = train_experiment(db_session, tmp_path, name="Second candidate")
    service = ExperimentService(db_session, artifact_base_dir=tmp_path)

    first_result = service.promote(first.id)
    assert first_result.lifecycle_status == ModelLifecycleStatus.CHAMPION

    second_result = service.promote(second.id)
    db_session.refresh(first)
    db_session.refresh(second)

    assert second_result.previous_champion_id == first.id
    assert second.lifecycle_status == ModelLifecycleStatus.CHAMPION.value
    assert first.lifecycle_status == ModelLifecycleStatus.CANDIDATE.value
    assert service.get_champion().champion.training_run_id == second.id

    first_events = service.get_experiment(first.id).lifecycle_events
    second_events = service.get_experiment(second.id).lifecycle_events
    assert any(event.event_type == "demoted" for event in first_events)
    assert any(event.event_type == "promoted" and event.previous_champion_id == first.id for event in second_events)


def test_champion_validation_rejects_ineligible_runs(db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    run = train_experiment(db_session, tmp_path, name="No artifact")
    run.artifact_path = None
    db_session.commit()

    try:
        ExperimentService(db_session, artifact_base_dir=tmp_path).promote(run.id)
    except ExperimentError as exc:
        assert exc.error_type == "missing_artifact"
    else:
        raise AssertionError("Missing artifacts should not be champion eligible.")

    try:
        ExperimentService(db_session, artifact_base_dir=tmp_path).promote(uuid4())
    except ExperimentError as exc:
        assert exc.error_type == "missing_training_run"
    else:
        raise AssertionError("Missing training runs should not be promoted.")


def test_archive_and_restore_preserve_completed_run(db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    run = train_experiment(db_session, tmp_path, name="Archivable")
    service = ExperimentService(db_session, artifact_base_dir=tmp_path)

    archive = service.archive(run.id)
    db_session.refresh(run)
    assert archive.lifecycle_status == ModelLifecycleStatus.ARCHIVED
    assert run.status == TrainingRunStatus.COMPLETED.value
    assert run.lifecycle_status == ModelLifecycleStatus.ARCHIVED.value

    restore = service.restore(run.id)
    db_session.refresh(run)
    assert restore.lifecycle_status == ModelLifecycleStatus.CANDIDATE
    assert run.lifecycle_status == ModelLifecycleStatus.CANDIDATE.value
    assert {event.event_type for event in service.get_experiment(run.id).lifecycle_events} == {"archived", "restored"}


def test_active_champion_cannot_be_archived(db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    run = train_experiment(db_session, tmp_path, name="Champion")
    service = ExperimentService(db_session, artifact_base_dir=tmp_path)
    service.promote(run.id)

    try:
        service.archive(run.id)
    except ExperimentError as exc:
        assert exc.error_type == "cannot_archive_champion"
    else:
        raise AssertionError("Active champion should not be archivable.")


def test_experiment_api_compare_champion_archive_restore(client: TestClient, db_session: Session, tmp_path: Path) -> None:
    add_monitoring_articles(db_session)
    first = TrainingService(db_session, artifact_base_dir=tmp_path / "models").train(
        experiment_training_config(name="API first")
    )
    second = TrainingService(db_session, artifact_base_dir=tmp_path / "models").train(
        experiment_training_config(name="API second", text_mode="title_only")
    )

    list_response = client.get("/api/v1/experiments")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 2
    assert list_response.json()["items"][0]["lifecycle_status"] == "candidate"

    detail_response = client.get(f"/api/v1/experiments/{first.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["model_display_name"] == "API first"
    assert detail_response.json()["validation_metrics"]
    assert detail_response.json()["test_metrics"]

    compare_response = client.post(
        "/api/v1/experiments/compare",
        json={
            "training_run_ids": [str(first.id), str(second.id)],
            "primary_metric": "f1",
            "metric_source": "test",
        },
    )
    assert compare_response.status_code == 200
    compare_payload = compare_response.json()
    assert compare_payload["comparability_status"] == "limited_comparability"
    assert compare_payload["comparability_warnings"]
    assert all(item["rank"] is None for item in compare_payload["items"])

    champion_before = client.get("/api/v1/models/champion")
    assert champion_before.status_code == 200
    assert champion_before.json()["champion"] is None

    promote_response = client.post(f"/api/v1/models/{first.id}/promote")
    assert promote_response.status_code == 200
    assert promote_response.json()["lifecycle_status"] == "champion"
    assert client.get("/api/v1/models/champion").json()["champion"]["training_run_id"] == str(first.id)

    archive_champion = client.post(f"/api/v1/models/{first.id}/archive")
    assert archive_champion.status_code == 400

    archive_second = client.post(f"/api/v1/models/{second.id}/archive")
    assert archive_second.status_code == 200
    assert archive_second.json()["lifecycle_status"] == "archived"

    restore_second = client.post(f"/api/v1/models/{second.id}/restore")
    assert restore_second.status_code == 200
    assert restore_second.json()["lifecycle_status"] == "candidate"


def test_invalid_comparison_config_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/experiments/compare",
        json={"training_run_ids": [str(uuid4()), str(uuid4())], "primary_metric": "confidence"},
    )

    assert response.status_code == 422
