from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel
from app.models.review import AnalysisReview
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, ModelLifecycleStatus


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_analysis(self, analysis_id: UUID) -> AnalysisRecord | None:
        return self.db.execute(
            select(AnalysisRecord)
            .options(selectinload(AnalysisRecord.review))
            .where(AnalysisRecord.id == analysis_id)
        ).scalars().first()

    def get_review(self, analysis_id: UUID) -> AnalysisReview | None:
        return self.db.execute(
            select(AnalysisReview).where(AnalysisReview.analysis_id == analysis_id)
        ).scalars().first()

    def add_review(self, review: AnalysisReview) -> AnalysisReview:
        self.db.add(review)
        return review

    def delete_review(self, review: AnalysisReview) -> None:
        self.db.delete(review)

    def queue_records(
        self,
        *,
        review_filter: str = "unreviewed",
        predicted_label: ArticleLabel | None = None,
        model_family: ModelFamily | None = None,
        model_type: ClassicalModelType | None = None,
        training_run_id: UUID | None = None,
        confidence_bucket: str = "all",
        high_confidence_threshold: float = 0.90,
        low_confidence_threshold: float = 0.60,
        search: str | None = None,
        sort: str = "recent",
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[AnalysisRecord], int]:
        statement = select(AnalysisRecord).outerjoin(AnalysisReview).options(selectinload(AnalysisRecord.review))
        count_statement = select(func.count()).select_from(AnalysisRecord).outerjoin(AnalysisReview)
        filters = self._analysis_filters(
            review_filter=review_filter,
            predicted_label=predicted_label,
            model_family=model_family,
            model_type=model_type,
            training_run_id=training_run_id,
            confidence_bucket=confidence_bucket,
            high_confidence_threshold=high_confidence_threshold,
            low_confidence_threshold=low_confidence_threshold,
            search=search,
        )
        for expression in filters:
            statement = statement.where(expression)
            count_statement = count_statement.where(expression)

        if sort == "low_confidence":
            statement = statement.order_by(AnalysisRecord.confidence.asc().nulls_last(), AnalysisRecord.created_at.desc())
        elif sort == "high_confidence":
            statement = statement.order_by(AnalysisRecord.confidence.desc().nulls_last(), AnalysisRecord.created_at.desc())
        else:
            statement = statement.order_by(AnalysisRecord.created_at.desc())

        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(statement.limit(limit).offset(offset)).scalars().all()
        return list(items), int(total)

    def reviewed_rows(
        self,
        *,
        training_run_id: UUID | None = None,
        model_family: ModelFamily | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[tuple[AnalysisRecord, AnalysisReview, MLTrainingRun | None]]:
        statement = (
            select(AnalysisRecord, AnalysisReview, MLTrainingRun)
            .join(AnalysisReview, AnalysisReview.analysis_id == AnalysisRecord.id)
            .outerjoin(MLTrainingRun, MLTrainingRun.id == AnalysisRecord.training_run_id)
            .order_by(AnalysisRecord.created_at.desc())
        )
        statement = self._apply_reviewed_scope(
            statement,
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
        )
        return list(self.db.execute(statement).all())

    def error_rows(
        self,
        *,
        training_run_id: UUID | None = None,
        model_family: ModelFamily | None = None,
        error_type: str | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[tuple[AnalysisRecord, AnalysisReview, MLTrainingRun | None]], int]:
        base = (
            select(AnalysisRecord, AnalysisReview, MLTrainingRun)
            .join(AnalysisReview, AnalysisReview.analysis_id == AnalysisRecord.id)
            .outerjoin(MLTrainingRun, MLTrainingRun.id == AnalysisRecord.training_run_id)
        )
        count_statement = (
            select(func.count())
            .select_from(AnalysisRecord)
            .join(AnalysisReview, AnalysisReview.analysis_id == AnalysisRecord.id)
        )
        base = self._apply_reviewed_scope(
            base,
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
        )
        count_statement = self._apply_reviewed_scope(
            count_statement,
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
        )
        filters = []
        if error_type == "false_positive":
            filters.append(AnalysisRecord.predicted_label == ArticleLabel.FAKE.value)
            filters.append(AnalysisReview.verified_label == ArticleLabel.REAL.value)
        elif error_type == "false_negative":
            filters.append(AnalysisRecord.predicted_label == ArticleLabel.REAL.value)
            filters.append(AnalysisReview.verified_label == ArticleLabel.FAKE.value)
        elif error_type == "correct_real":
            filters.append(AnalysisRecord.predicted_label == ArticleLabel.REAL.value)
            filters.append(AnalysisReview.verified_label == ArticleLabel.REAL.value)
        elif error_type == "correct_fake":
            filters.append(AnalysisRecord.predicted_label == ArticleLabel.FAKE.value)
            filters.append(AnalysisReview.verified_label == ArticleLabel.FAKE.value)
        if min_confidence is not None:
            filters.append(AnalysisRecord.confidence >= min_confidence)
        if max_confidence is not None:
            filters.append(AnalysisRecord.confidence <= max_confidence)
        for expression in filters:
            base = base.where(expression)
            count_statement = count_statement.where(expression)

        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(
            base.order_by(AnalysisRecord.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return list(items), int(total)

    def review_statistics(self) -> tuple[int, list[tuple[AnalysisRecord, AnalysisReview]], list[tuple[UUID | None, int]]]:
        total = self.db.execute(select(func.count()).select_from(AnalysisRecord)).scalar_one()
        reviewed = self.db.execute(
            select(AnalysisRecord, AnalysisReview).join(AnalysisReview, AnalysisReview.analysis_id == AnalysisRecord.id)
        ).all()
        analysis_counts = self.db.execute(
            select(AnalysisRecord.training_run_id, func.count()).group_by(AnalysisRecord.training_run_id)
        ).all()
        return int(total), list(reviewed), [(row[0], int(row[1])) for row in analysis_counts]

    @staticmethod
    def _analysis_filters(
        *,
        review_filter: str,
        predicted_label: ArticleLabel | None,
        model_family: ModelFamily | None,
        model_type: ClassicalModelType | None,
        training_run_id: UUID | None,
        confidence_bucket: str,
        high_confidence_threshold: float,
        low_confidence_threshold: float,
        search: str | None,
    ) -> list:
        filters = []
        if review_filter == "unreviewed":
            filters.append(AnalysisReview.id.is_(None))
        elif review_filter == "reviewed":
            filters.append(AnalysisReview.id.is_not(None))
        elif review_filter == "correct":
            filters.append(AnalysisReview.id.is_not(None))
            filters.append(AnalysisRecord.predicted_label == AnalysisReview.verified_label)
        elif review_filter == "incorrect":
            filters.append(AnalysisReview.id.is_not(None))
            filters.append(AnalysisRecord.predicted_label != AnalysisReview.verified_label)
        if predicted_label is not None:
            filters.append(AnalysisRecord.predicted_label == predicted_label.value)
        if model_family is not None:
            filters.append(AnalysisRecord.model_family == model_family.value)
        if model_type is not None:
            filters.append(AnalysisRecord.model_type == model_type.value)
        if training_run_id is not None:
            filters.append(AnalysisRecord.training_run_id == training_run_id)
        if confidence_bucket == "high":
            filters.append(AnalysisRecord.confidence >= high_confidence_threshold)
        elif confidence_bucket == "low":
            filters.append(AnalysisRecord.confidence < low_confidence_threshold)
        if search:
            search_pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    AnalysisRecord.title.ilike(search_pattern),
                    AnalysisRecord.content.ilike(search_pattern),
                )
            )
        return filters

    @staticmethod
    def _apply_reviewed_scope(
        statement: Select,
        *,
        training_run_id: UUID | None,
        model_family: ModelFamily | None,
        created_after: datetime | None,
        created_before: datetime | None,
    ) -> Select:
        if training_run_id is not None:
            statement = statement.where(AnalysisRecord.training_run_id == training_run_id)
        if model_family is not None:
            statement = statement.where(AnalysisRecord.model_family == model_family.value)
        if created_after is not None:
            statement = statement.where(AnalysisRecord.created_at >= created_after)
        if created_before is not None:
            statement = statement.where(AnalysisRecord.created_at <= created_before)
        return statement


def has_explanation(record: AnalysisRecord) -> bool:
    return record.explanation_status == ExplanationStatus.GENERATED


def article_preview(content: str | None, limit: int = 220) -> str | None:
    if not content:
        return None
    compact = " ".join(content.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3].rstrip()}..."
