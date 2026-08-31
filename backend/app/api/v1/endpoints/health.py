from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.ml.artifacts import ArtifactError, ArtifactStore
from app.ml.transformer_artifacts import TransformerArtifactStore
from app.models.training import ModelFamily
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.health import ComponentStatus, HealthResponse, ProcessMetricsResponse, ReadinessResponse, SystemInfoResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name)


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness_check(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    components = {
        "database": _database_status(db),
        "model_storage": _directory_status(getattr(request.app.state, "artifact_base_dir", None) or settings.trained_models_dir),
        "data_storage": _directory_status(getattr(request.app.state, "raw_data_dir", None) or settings.data_raw_dir),
        "schema": _schema_status(db),
        "champion_model": _champion_status(db, getattr(request.app.state, "artifact_base_dir", None)),
    }
    ready = all(component.status in {"ok", "not_required"} for component in components.values())
    payload = ReadinessResponse(
        status="ready" if ready else "not_ready",
        service=settings.app_name,
        environment=settings.app_env,
        components=components,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload.model_dump(mode="json"),
    )


@router.get("/system/info", response_model=SystemInfoResponse)
async def system_info() -> SystemInfoResponse:
    return SystemInfoResponse(
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        api_version=settings.api_v1_prefix,
        docs_enabled=settings.docs_enabled,
        capabilities=[
            "dataset_ingestion",
            "classical_training",
            "transformer_training",
            "inference",
            "explainability",
            "analysis_history",
            "monitoring",
            "experiment_tracking",
            "champion_selection",
            "readiness_checks",
        ],
    )


@router.get("/system/metrics", response_model=ProcessMetricsResponse)
async def process_metrics(request: Request) -> ProcessMetricsResponse:
    metrics = getattr(request.app.state, "process_metrics", None)
    snapshot = metrics.snapshot() if metrics is not None else {}
    return ProcessMetricsResponse(**snapshot)


def _database_status(db: Session) -> ComponentStatus:
    try:
        db.execute(text("SELECT 1"))
        return ComponentStatus(status="ok")
    except SQLAlchemyError:
        return ComponentStatus(status="error", message="Database connection failed.")


def _schema_status(db: Session) -> ComponentStatus:
    required_tables = {
        "news_articles",
        "dataset_import_runs",
        "ml_training_runs",
        "analysis_records",
        "model_monitoring_profiles",
        "model_lifecycle_events",
    }
    try:
        existing = set(inspect(db.get_bind()).get_table_names())
        missing = sorted(required_tables - existing)
        if missing:
            return ComponentStatus(status="error", message=f"Missing required tables: {', '.join(missing)}")
        return ComponentStatus(status="ok")
    except SQLAlchemyError:
        return ComponentStatus(status="error", message="Schema inspection failed.")


def _directory_status(path) -> ComponentStatus:
    try:
        resolved = path.resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        probe = resolved / ".readiness-check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return ComponentStatus(status="ok")
    except OSError:
        return ComponentStatus(status="error", message="Required storage is not writable.")


def _champion_status(db: Session, artifact_base_dir) -> ComponentStatus:
    try:
        champion = TrainingRunRepository(db).get_champion()
        if champion is None:
            return ComponentStatus(status="not_required", message="No champion has been selected.")
        if not champion.artifact_path:
            return ComponentStatus(status="error", message="Champion artifact metadata is missing.")
        try:
            if champion.model_family == ModelFamily.TRANSFORMER.value:
                TransformerArtifactStore(artifact_base_dir).load_metadata(champion.artifact_path)
            else:
                ArtifactStore(artifact_base_dir).validate_metadata(champion.artifact_path)
        except ArtifactError:
            return ComponentStatus(status="error", message="Champion artifact integrity check failed.")
        return ComponentStatus(status="ok")
    except SQLAlchemyError:
        return ComponentStatus(status="error", message="Champion metadata check failed.")
