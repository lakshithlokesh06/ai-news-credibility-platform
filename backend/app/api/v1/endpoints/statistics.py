from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.statistics import DatasetStatisticsResponse
from app.services.statistics import DatasetStatisticsService

router = APIRouter(prefix="/dataset-statistics")


@router.get("", response_model=DatasetStatisticsResponse)
async def retrieve_dataset_statistics(
    db: Session = Depends(get_db),
) -> DatasetStatisticsResponse:
    service = DatasetStatisticsService(db)
    return service.calculate()

