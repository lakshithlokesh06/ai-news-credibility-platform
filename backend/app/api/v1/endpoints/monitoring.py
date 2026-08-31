from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.monitoring.config import MonitoringError
from app.monitoring.service import MonitoringService
from app.schemas.monitoring import (
    ModelMonitoringResponse,
    MonitoringConfig,
    MonitoringOverviewResponse,
    MonitoringProfileResponse,
)

router = APIRouter(prefix="/monitoring")


def _config_from_query(
    window_size: int = Query(default=100, ge=5, le=500),
    minimum_sample_count: int = Query(default=10, ge=2, le=100),
    low_confidence_threshold: float = Query(default=0.60, ge=0.0, le=1.0),
    high_confidence_threshold: float = Query(default=0.90, ge=0.0, le=1.0),
    psi_warning_threshold: float = Query(default=0.10, ge=0.0, le=1.0),
    psi_drift_threshold: float = Query(default=0.25, ge=0.0, le=2.0),
    js_warning_threshold: float = Query(default=0.05, ge=0.0, le=1.0),
    js_drift_threshold: float = Query(default=0.15, ge=0.0, le=1.0),
    ks_warning_threshold: float = Query(default=0.20, ge=0.0, le=1.0),
    ks_drift_threshold: float = Query(default=0.35, ge=0.0, le=1.0),
) -> MonitoringConfig:
    return MonitoringConfig(
        window_size=window_size,
        minimum_sample_count=minimum_sample_count,
        low_confidence_threshold=low_confidence_threshold,
        high_confidence_threshold=high_confidence_threshold,
        psi_warning_threshold=psi_warning_threshold,
        psi_drift_threshold=psi_drift_threshold,
        js_warning_threshold=js_warning_threshold,
        js_drift_threshold=js_drift_threshold,
        ks_warning_threshold=ks_warning_threshold,
        ks_drift_threshold=ks_drift_threshold,
    )


def _monitoring_error(exc: MonitoringError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if exc.error_type == "missing_training_run"
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(
        status_code=status_code,
        detail={"message": str(exc), "error_type": exc.error_type},
    )


@router.get("", response_model=MonitoringOverviewResponse)
async def monitoring_overview(
    http_request: Request,
    config: MonitoringConfig = Depends(_config_from_query),
    db: Session = Depends(get_db),
) -> MonitoringOverviewResponse:
    service = MonitoringService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    return service.overview(config)


@router.get("/models/{training_run_id}", response_model=ModelMonitoringResponse)
async def monitor_model(
    training_run_id: UUID,
    http_request: Request,
    config: MonitoringConfig = Depends(_config_from_query),
    db: Session = Depends(get_db),
) -> ModelMonitoringResponse:
    service = MonitoringService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    try:
        return service.monitor_model(training_run_id, config)
    except MonitoringError as exc:
        raise _monitoring_error(exc) from exc


@router.post("/models/{training_run_id}/reference-profile", response_model=MonitoringProfileResponse)
async def refresh_reference_profile(
    training_run_id: UUID,
    http_request: Request,
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> MonitoringProfileResponse:
    service = MonitoringService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    try:
        return MonitoringProfileResponse.model_validate(
            service.generate_reference_profile(training_run_id, refresh=True)
        )
    except MonitoringError as exc:
        raise _monitoring_error(exc) from exc
