from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.article import DatasetImportRun


class ImportRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, import_run: DatasetImportRun) -> DatasetImportRun:
        self.db.add(import_run)
        return import_run

    def get(self, import_run_id: UUID) -> DatasetImportRun | None:
        return self.db.get(DatasetImportRun, import_run_id)

    def list_runs(self, *, limit: int = 25, offset: int = 0) -> tuple[list[DatasetImportRun], int]:
        total = self.db.execute(select(func.count()).select_from(DatasetImportRun)).scalar_one()
        items = self.db.execute(
            select(DatasetImportRun)
            .order_by(DatasetImportRun.started_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
        return list(items), int(total)

