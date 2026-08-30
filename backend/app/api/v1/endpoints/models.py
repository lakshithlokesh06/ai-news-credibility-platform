from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.experiments import ChampionResponse, LifecycleActionResponse
from app.services.experiments import ExperimentError, ExperimentService

router = APIRouter(prefix="/models")


def _experiment_error(exc: ExperimentError) -> HTTPException:
    status_code = 404 if exc.error_type == "missing_training_run" else 400
    return HTTPException(status_code=status_code, detail={"message": str(exc), "error_type": exc.error_type})


@router.get("/champion", response_model=ChampionResponse)
async def get_champion(
    http_request: Request,
    db: Session = Depends(get_db),
) -> ChampionResponse:
    return ExperimentService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    ).get_champion()


@router.post("/{training_run_id}/promote", response_model=LifecycleActionResponse)
async def promote_model(
    training_run_id: UUID,
    http_request: Request,
    db: Session = Depends(get_db),
) -> LifecycleActionResponse:
    try:
        return ExperimentService(
            db,
            artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
        ).promote(training_run_id)
    except ExperimentError as exc:
        raise _experiment_error(exc) from exc


@router.post("/{training_run_id}/archive", response_model=LifecycleActionResponse)
async def archive_model(
    training_run_id: UUID,
    http_request: Request,
    db: Session = Depends(get_db),
) -> LifecycleActionResponse:
    try:
        return ExperimentService(
            db,
            artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
        ).archive(training_run_id)
    except ExperimentError as exc:
        raise _experiment_error(exc) from exc


@router.post("/{training_run_id}/restore", response_model=LifecycleActionResponse)
async def restore_model(
    training_run_id: UUID,
    http_request: Request,
    db: Session = Depends(get_db),
) -> LifecycleActionResponse:
    try:
        return ExperimentService(
            db,
            artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
        ).restore(training_run_id)
    except ExperimentError as exc:
        raise _experiment_error(exc) from exc
