from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily
from app.review.service import ReviewError, ReviewService
from app.schemas.review import (
    CalibrationResponse,
    ConfidenceBucket,
    ErrorAnalysisResponse,
    ErrorType,
    PaginatedReviewQueueResponse,
    ProductionPerformanceResponse,
    QueueSort,
    ReviewFilter,
    ReviewStatisticsResponse,
)

router = APIRouter(prefix="/reviews")


def _review_error(exc: ReviewError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if exc.error_type in {"analysis_not_found", "review_not_found", "training_run_not_found"}
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(status_code=status_code, detail={"message": str(exc), "error_type": exc.error_type})


@router.get("/queue", response_model=PaginatedReviewQueueResponse)
async def review_queue(
    review_filter: ReviewFilter = Query(default="unreviewed"),
    predicted_label: ArticleLabel | None = Query(default=None),
    model_family: ModelFamily | None = Query(default=None),
    model_type: ClassicalModelType | None = Query(default=None),
    training_run_id: UUID | None = Query(default=None),
    confidence_bucket: ConfidenceBucket = Query(default="all"),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    sort: QueueSort = Query(default="recent"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> PaginatedReviewQueueResponse:
    try:
        return ReviewService(db).queue(
            review_filter=review_filter,
            predicted_label=predicted_label,
            model_family=model_family,
            model_type=model_type,
            training_run_id=training_run_id,
            confidence_bucket=confidence_bucket,
            search=search,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    except ReviewError as exc:
        raise _review_error(exc) from exc


@router.get("/statistics", response_model=ReviewStatisticsResponse)
async def review_statistics(
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> ReviewStatisticsResponse:
    return ReviewService(db).statistics()


@router.get("/performance", response_model=ProductionPerformanceResponse)
async def reviewed_performance(
    training_run_id: UUID | None = Query(default=None),
    model_family: ModelFamily | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> ProductionPerformanceResponse:
    try:
        return ReviewService(db).performance(
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
        )
    except ReviewError as exc:
        raise _review_error(exc) from exc


@router.get("/calibration", response_model=CalibrationResponse)
async def reviewed_calibration(
    training_run_id: UUID | None = Query(default=None),
    model_family: ModelFamily | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    bins: int = Query(default=settings.calibration_default_bins, ge=2, le=20),
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> CalibrationResponse:
    try:
        return ReviewService(db).calibration(
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
            bins=bins,
        )
    except ReviewError as exc:
        raise _review_error(exc) from exc


@router.get("/errors", response_model=ErrorAnalysisResponse)
async def reviewed_errors(
    training_run_id: UUID | None = Query(default=None),
    model_family: ModelFamily | None = Query(default=None),
    error_type: ErrorType | None = Query(default=None),
    min_confidence: float | None = Query(default=None, ge=0, le=1),
    max_confidence: float | None = Query(default=None, ge=0, le=1),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> ErrorAnalysisResponse:
    try:
        return ReviewService(db).errors(
            training_run_id=training_run_id,
            model_family=model_family,
            error_type=error_type,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )
    except ReviewError as exc:
        raise _review_error(exc) from exc
