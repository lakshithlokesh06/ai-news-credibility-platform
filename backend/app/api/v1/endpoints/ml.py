from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ml.comparison import ModelComparisonService
from app.ml.inference import InferenceError, InferenceService
from app.ml.training_service import TrainingService
from app.models.training import TrainingRunStatus
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.ml import (
    MLTrainingRunResponse,
    ModelComparisonResponse,
    PaginatedTrainingRunsResponse,
    PredictionRequest,
    PredictionResponse,
    TrainingRunCreate,
)

router = APIRouter(prefix="/ml")


@router.post(
    "/training-runs",
    response_model=MLTrainingRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_training_run(
    request: TrainingRunCreate,
    http_request: Request,
    db: Session = Depends(get_db),
) -> MLTrainingRunResponse:
    service = TrainingService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    training_run = service.train(request)
    if training_run.status == TrainingRunStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Training could not safely proceed.",
                "training_run_id": str(training_run.id),
                "error": training_run.error_summary,
            },
        )
    return training_run


@router.get("/training-runs", response_model=PaginatedTrainingRunsResponse)
async def list_training_runs(
    run_status: TrainingRunStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedTrainingRunsResponse:
    repository = TrainingRunRepository(db)
    items, total = repository.list_runs(status=run_status, limit=limit, offset=offset)
    return PaginatedTrainingRunsResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/training-runs/{training_run_id}", response_model=MLTrainingRunResponse)
async def retrieve_training_run(
    training_run_id: UUID,
    db: Session = Depends(get_db),
) -> MLTrainingRunResponse:
    repository = TrainingRunRepository(db)
    training_run = repository.get(training_run_id)
    if training_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training run not found.")
    return training_run


@router.post("/models/{training_run_id}/predict", response_model=PredictionResponse)
async def predict_with_model(
    training_run_id: UUID,
    request: PredictionRequest,
    http_request: Request,
    db: Session = Depends(get_db),
) -> PredictionResponse:
    service = InferenceService(
        db,
        artifact_base_dir=getattr(http_request.app.state, "artifact_base_dir", None),
    )
    try:
        return service.predict(training_run_id, request)
    except InferenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/model-comparison", response_model=ModelComparisonResponse)
async def compare_models(
    metric_source: str = Query(default="test", pattern="^(validation|test)$"),
    primary_metric: str = Query(default="f1", pattern="^(accuracy|precision|recall|f1|roc_auc)$"),
    db: Session = Depends(get_db),
) -> ModelComparisonResponse:
    service = ModelComparisonService(db)
    return service.compare(metric_source=metric_source, primary_metric=primary_metric)

