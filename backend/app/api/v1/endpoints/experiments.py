from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.training import ClassicalModelType, ModelFamily, ModelLifecycleStatus, TrainingRunStatus
from app.schemas.experiments import (
    ExperimentComparisonRequest,
    ExperimentComparisonResponse,
    ExperimentDetail,
    PaginatedExperimentsResponse,
)
from app.services.experiments import ExperimentError, ExperimentService

router = APIRouter(prefix="/experiments")


def _experiment_error(exc: ExperimentError) -> HTTPException:
    status_code = status.HTTP_404_NOT_FOUND if exc.error_type == "missing_training_run" else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=status_code, detail={"message": str(exc), "error_type": exc.error_type})


@router.get("", response_model=PaginatedExperimentsResponse)
async def list_experiments(
    http_request: Request,
    run_status: TrainingRunStatus | None = Query(default=None, alias="status"),
    model_family: ModelFamily | None = None,
    model_type: ClassicalModelType | None = None,
    lifecycle_status: ModelLifecycleStatus | None = None,
    champion: bool | None = None,
    trained_after: datetime | None = None,
    trained_before: datetime | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedExperimentsResponse:
    service = ExperimentService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    return service.list_experiments(
        status=run_status,
        model_family=model_family,
        model_type=model_type,
        lifecycle_status=lifecycle_status,
        champion=champion,
        trained_after=trained_after,
        trained_before=trained_before,
        limit=limit,
        offset=offset,
    )


@router.post("/compare", response_model=ExperimentComparisonResponse)
async def compare_experiments(
    request: ExperimentComparisonRequest,
    http_request: Request,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> ExperimentComparisonResponse:
    service = ExperimentService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    try:
        return service.compare(request)
    except ExperimentError as exc:
        raise _experiment_error(exc) from exc


@router.get("/{training_run_id}", response_model=ExperimentDetail)
async def retrieve_experiment(
    training_run_id: UUID,
    http_request: Request,
    db: Session = Depends(get_db),
) -> ExperimentDetail:
    service = ExperimentService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    try:
        return service.get_experiment(training_run_id)
    except ExperimentError as exc:
        raise _experiment_error(exc) from exc
