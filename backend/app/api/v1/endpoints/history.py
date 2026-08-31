from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily
from app.review.service import ReviewError, ReviewService
from app.schemas.history import (
    AnalysisHistoryDetail,
    DeleteHistoryResponse,
    HistoryStatisticsResponse,
    PaginatedHistoryResponse,
)
from app.schemas.review import DeleteReviewResponse, ReviewFilter, ReviewResponse, ReviewUpsertRequest
from app.services.history import AnalysisHistoryService, HistoryError

router = APIRouter(prefix="/history")


def _history_error(exc: HistoryError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if exc.error_type == "analysis_not_found"
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(
        status_code=status_code,
        detail={"message": str(exc), "error_type": exc.error_type},
    )


def _review_error(exc: ReviewError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if exc.error_type in {"analysis_not_found", "review_not_found"}
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(status_code=status_code, detail={"message": str(exc), "error_type": exc.error_type})


@router.get("", response_model=PaginatedHistoryResponse)
async def list_history(
    predicted_label: ArticleLabel | None = Query(default=None),
    model_family: ModelFamily | None = Query(default=None),
    model_type: ClassicalModelType | None = Query(default=None),
    training_run_id: UUID | None = Query(default=None),
    explanation_available: bool | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    review_filter: ReviewFilter | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedHistoryResponse:
    service = AnalysisHistoryService(db)
    items, total = service.list_summaries(
        predicted_label=predicted_label,
        model_family=model_family,
        model_type=model_type,
        training_run_id=training_run_id,
        explanation_available=explanation_available,
        created_after=created_after,
        created_before=created_before,
        search=search,
        review_filter=review_filter if review_filter != "all" else None,
        limit=limit,
        offset=offset,
    )
    return PaginatedHistoryResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/statistics", response_model=HistoryStatisticsResponse)
async def history_statistics(db: Session = Depends(get_db)) -> HistoryStatisticsResponse:
    return AnalysisHistoryService(db).statistics()


@router.get("/{analysis_id}", response_model=AnalysisHistoryDetail)
async def history_detail(
    analysis_id: UUID,
    db: Session = Depends(get_db),
) -> AnalysisHistoryDetail:
    try:
        return AnalysisHistoryService(db).detail(analysis_id)
    except HistoryError as exc:
        raise _history_error(exc) from exc


@router.put("/{analysis_id}/review", response_model=ReviewResponse)
async def upsert_history_review(
    analysis_id: UUID,
    request: ReviewUpsertRequest,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    try:
        return ReviewService(db).upsert_review(analysis_id, request)
    except ReviewError as exc:
        raise _review_error(exc) from exc


@router.delete("/{analysis_id}/review", response_model=DeleteReviewResponse)
async def delete_history_review(
    analysis_id: UUID,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> DeleteReviewResponse:
    try:
        return ReviewService(db).delete_review(analysis_id)
    except ReviewError as exc:
        raise _review_error(exc) from exc


@router.delete("/{analysis_id}", response_model=DeleteHistoryResponse)
async def delete_history(
    analysis_id: UUID,
    db: Session = Depends(get_db),
) -> DeleteHistoryResponse:
    try:
        return AnalysisHistoryService(db).delete(analysis_id)
    except HistoryError as exc:
        raise _history_error(exc) from exc
