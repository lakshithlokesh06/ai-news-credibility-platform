from collections.abc import Generator
from pathlib import Path
from threading import BoundedSemaphore
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings, settings
from app.core.rate_limit import InMemoryRateLimiter
from app.db.session import get_db
from app.main import create_app
from app.ml.artifacts import ArtifactError, resolve_artifact_dir
from app.schemas.ml import PredictionRequest
from app.services.ingestion import DatasetImportError, DatasetIngestionService


def test_production_configuration_rejects_unsafe_cors_and_debug() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            debug=True,
            docs_enabled=False,
            backend_cors_origins="https://example.com",
        )
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            debug=False,
            docs_enabled=False,
            backend_cors_origins="*",
        )
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            debug=False,
            docs_enabled=True,
            backend_cors_origins="https://example.com",
        )


def test_request_id_and_security_headers_are_returned(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "test-request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-123"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "x" * 200})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "x" * 200
    assert len(response.headers["X-Request-ID"]) <= 64


def test_oversized_article_is_rejected_without_echoing_content(client: TestClient) -> None:
    content = "a" * (settings.max_article_content_chars + 1)
    response = client.post(f"/api/v1/ml/models/{uuid4()}/predict", json={"content": content})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert content not in response.text


def test_prediction_request_combined_article_limit() -> None:
    with pytest.raises(ValidationError):
        PredictionRequest(
            title="t" * settings.max_article_title_chars,
            content="c" * (settings.max_combined_article_chars - settings.max_article_title_chars + 1),
        )


def test_dataset_import_path_and_file_size_are_restricted(db_session, tmp_path: Path, monkeypatch) -> None:
    service = DatasetIngestionService(db_session, raw_data_dir=tmp_path)
    with pytest.raises(DatasetImportError):
        service.resolve_import_path("../outside.csv")
    with pytest.raises(DatasetImportError):
        service.resolve_import_path("/tmp/outside.csv")

    large_file = tmp_path / "large.csv"
    large_file.write_text("title,content,label\n", encoding="utf-8")
    monkeypatch.setattr(settings, "max_dataset_file_bytes", 4)
    with pytest.raises(DatasetImportError):
        service.resolve_import_path("large.csv")


def test_artifact_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ArtifactError):
        resolve_artifact_dir("../model", tmp_path)
    with pytest.raises(ArtifactError):
        resolve_artifact_dir("/tmp/model", tmp_path)


def test_rate_limit_returns_429(client: TestClient) -> None:
    client.app.state.rate_limiters = {
        "prediction": InMemoryRateLimiter(limit=1, window_seconds=60),
    }
    body = {"content": "short text"}

    assert client.post(f"/api/v1/ml/models/{uuid4()}/predict", json=body).status_code == 400
    response = client.post(f"/api/v1/ml/models/{uuid4()}/predict", json=body)

    assert response.status_code == 429
    assert response.headers["Retry-After"]
    assert response.json()["error"]["code"] == "rate_limited"


def test_training_capacity_exhaustion_returns_503(client: TestClient) -> None:
    semaphore = BoundedSemaphore(1)
    semaphore.acquire()
    client.app.state.capacity_semaphores = {"training": semaphore}

    response = client.post("/api/v1/ml/training-runs", json={"model_type": "logistic_regression"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "training_capacity_exhausted"
    semaphore.release()


def test_readiness_reports_healthy_dependencies(client: TestClient) -> None:
    response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["components"]["database"]["status"] == "ok"
    assert payload["components"]["model_storage"]["status"] == "ok"
    assert payload["components"]["champion_model"]["status"] in {"ok", "not_required"}


def test_readiness_reports_database_failure(tmp_path: Path) -> None:
    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise SQLAlchemyError("database unavailable")

        def get_bind(self):
            raise SQLAlchemyError("schema unavailable")

    app = create_app()
    app.state.raw_data_dir = tmp_path
    app.state.artifact_base_dir = tmp_path / "models"

    def broken_db() -> Generator[BrokenSession, None, None]:
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/readiness")

    assert response.status_code == 503
    assert response.json()["components"]["database"]["status"] == "error"


def test_system_info_and_metrics_are_safe(client: TestClient) -> None:
    info = client.get("/api/v1/system/info")
    metrics = client.get("/api/v1/system/metrics")

    assert info.status_code == 200
    assert info.json()["version"]
    assert "database_url" not in info.text.lower()
    assert metrics.status_code == 200
    assert "article" not in metrics.text.lower()
