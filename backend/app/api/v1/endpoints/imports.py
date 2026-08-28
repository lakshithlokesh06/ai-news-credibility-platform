from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.import_run_repository import ImportRunRepository
from app.schemas.import_run import (
    DatasetImportRequest,
    DatasetImportRunResponse,
    PaginatedImportRunsResponse,
)
from app.services.ingestion import DatasetIngestionService

router = APIRouter(prefix="/dataset-imports")


@router.get("", response_model=PaginatedImportRunsResponse)
async def list_dataset_import_runs(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedImportRunsResponse:
    repository = ImportRunRepository(db)
    items, total = repository.list_runs(limit=limit, offset=offset)
    return PaginatedImportRunsResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{import_run_id}", response_model=DatasetImportRunResponse)
async def retrieve_dataset_import_run(
    import_run_id: UUID,
    db: Session = Depends(get_db),
) -> DatasetImportRunResponse:
    repository = ImportRunRepository(db)
    import_run = repository.get(import_run_id)
    if import_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset import run not found.",
        )
    return import_run


@router.post("", response_model=DatasetImportRunResponse, status_code=status.HTTP_201_CREATED)
async def import_dataset(
    request: DatasetImportRequest,
    http_request: Request,
    db: Session = Depends(get_db),
) -> DatasetImportRunResponse:
    service = DatasetIngestionService(
        db,
        raw_data_dir=getattr(http_request.app.state, "raw_data_dir", None),
    )
    return service.import_csv(request)
