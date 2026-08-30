from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, ModelFamily


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, analysis: AnalysisRecord) -> AnalysisRecord:
        self.db.add(analysis)
        return analysis

    def get(self, analysis_id: UUID) -> AnalysisRecord | None:
        return self.db.get(AnalysisRecord, analysis_id)

    def delete(self, analysis: AnalysisRecord) -> None:
        self.db.delete(analysis)

    def list_records(
        self,
        *,
        predicted_label: ArticleLabel | None = None,
        model_family: ModelFamily | None = None,
        model_type: ClassicalModelType | None = None,
        training_run_id: UUID | None = None,
        explanation_available: bool | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        search: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[AnalysisRecord], int]:
        statement = select(AnalysisRecord)
        count_statement = select(func.count()).select_from(AnalysisRecord)
        filters = []
        if predicted_label is not None:
            filters.append(AnalysisRecord.predicted_label == predicted_label.value)
        if model_family is not None:
            filters.append(AnalysisRecord.model_family == model_family.value)
        if model_type is not None:
            filters.append(AnalysisRecord.model_type == model_type.value)
        if training_run_id is not None:
            filters.append(AnalysisRecord.training_run_id == training_run_id)
        if explanation_available is True:
            filters.append(AnalysisRecord.explanation_status == ExplanationStatus.GENERATED)
        elif explanation_available is False:
            filters.append(AnalysisRecord.explanation_status != ExplanationStatus.GENERATED)
        if created_after is not None:
            filters.append(AnalysisRecord.created_at >= created_after)
        if created_before is not None:
            filters.append(AnalysisRecord.created_at <= created_before)
        if search:
            search_pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    AnalysisRecord.title.ilike(search_pattern),
                    AnalysisRecord.content.ilike(search_pattern),
                )
            )

        for expression in filters:
            statement = statement.where(expression)
            count_statement = count_statement.where(expression)

        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(
            statement.order_by(AnalysisRecord.created_at.desc()).limit(limit).offset(offset)
        ).scalars().all()
        return list(items), int(total)

    def all_for_statistics(self) -> list[AnalysisRecord]:
        return list(
            self.db.execute(select(AnalysisRecord).order_by(AnalysisRecord.created_at.asc())).scalars().all()
        )
