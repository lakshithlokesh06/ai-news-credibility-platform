from collections import Counter, defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.history import (
    AnalysisExplanationDetail,
    AnalysisHistoryDetail,
    AnalysisHistorySummary,
    DeleteHistoryResponse,
    HistoryDistributionItem,
    HistoryStatisticsResponse,
    RecentHistoryVolumeItem,
    TrainingRunHistoryItem,
)
from app.schemas.ml import ExplanationRequest, ExplanationResponse, PredictionRequest, PredictionResponse
from app.schemas.review import AnalysisReviewInfo


class HistoryError(ValueError):
    def __init__(self, message: str, error_type: str = "history_error") -> None:
        super().__init__(message)
        self.error_type = error_type


class AnalysisHistoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AnalysisRepository(db)

    def create_from_prediction(
        self,
        *,
        training_run: MLTrainingRun,
        request: PredictionRequest,
        prediction: PredictionResponse,
    ) -> AnalysisRecord:
        now = datetime.now(UTC)
        analysis = AnalysisRecord(
            training_run_id=training_run.id,
            model_family=prediction.model_family.value,
            model_type=prediction.model_type.value,
            model_name=prediction.model_name,
            model_display_name=training_run.model_display_name,
            title=request.title,
            content=request.content,
            text_composition_mode=str(training_run.text_composition_config.get("mode"))
            if training_run.text_composition_config
            else None,
            predicted_label=prediction.predicted_label.value,
            real_probability=prediction.real_probability,
            fake_probability=prediction.fake_probability,
            confidence=prediction.confidence,
            probability_method=prediction.probability_method,
            explanation_status=ExplanationStatus.NOT_REQUESTED,
            influences_toward_real=[],
            influences_toward_fake=[],
            explanation_limitations=[],
            created_at=now,
            updated_at=now,
        )
        self.repository.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def validate_for_explanation(
        self,
        *,
        analysis_id: UUID,
        training_run_id: UUID,
        request: ExplanationRequest,
    ) -> AnalysisRecord:
        analysis = self.get_or_raise(analysis_id)
        if analysis.training_run_id != training_run_id:
            raise HistoryError("Analysis record does not belong to this training run.", "training_run_mismatch")
        if (analysis.title or "") != (request.title or "") or (analysis.content or "") != (request.content or ""):
            raise HistoryError("Explanation input does not match the saved analysis record.", "analysis_input_mismatch")
        return analysis

    def attach_explanation(self, analysis: AnalysisRecord, explanation: ExplanationResponse) -> AnalysisRecord:
        now = datetime.now(UTC)
        analysis.explanation_status = ExplanationStatus.GENERATED
        analysis.explanation_method = explanation.explanation_method
        analysis.explained_class = explanation.explained_class.value
        analysis.influences_toward_real = [
            item.model_dump(mode="json") for item in explanation.influences_toward_real
        ]
        analysis.influences_toward_fake = [
            item.model_dump(mode="json") for item in explanation.influences_toward_fake
        ]
        analysis.explanation_limitations = explanation.limitations
        analysis.explanation_message = explanation.message
        analysis.explanation_generated_at = now
        analysis.updated_at = now
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_or_raise(self, analysis_id: UUID) -> AnalysisRecord:
        analysis = self.repository.get(analysis_id)
        if analysis is None:
            raise HistoryError("Analysis record was not found.", "analysis_not_found")
        return analysis

    def list_summaries(self, **filters) -> tuple[list[AnalysisHistorySummary], int]:
        records, total = self.repository.list_records(**filters)
        return [self._summary(record) for record in records], total

    def detail(self, analysis_id: UUID) -> AnalysisHistoryDetail:
        return self._detail(self.get_or_raise(analysis_id))

    def delete(self, analysis_id: UUID) -> DeleteHistoryResponse:
        analysis = self.get_or_raise(analysis_id)
        self.repository.delete(analysis)
        self.db.commit()
        return DeleteHistoryResponse(
            analysis_id=analysis_id,
            deleted=True,
            message="Analysis history record deleted. Training runs, datasets, and model artifacts were not changed.",
        )

    def statistics(self) -> HistoryStatisticsResponse:
        records = self.repository.all_for_statistics()
        total = len(records)
        real_count = sum(1 for record in records if record.predicted_label == ArticleLabel.REAL.value)
        fake_count = sum(1 for record in records if record.predicted_label == ArticleLabel.FAKE.value)
        explained_count = sum(1 for record in records if record.explanation_status == ExplanationStatus.GENERATED)

        confidence_values = [record.confidence for record in records if record.confidence is not None]
        real_confidence_values = [
            record.confidence
            for record in records
            if record.predicted_label == ArticleLabel.REAL.value and record.confidence is not None
        ]
        fake_confidence_values = [
            record.confidence
            for record in records
            if record.predicted_label == ArticleLabel.FAKE.value and record.confidence is not None
        ]

        family_counts = Counter(record.model_family for record in records)
        type_counts = Counter(record.model_type for record in records)
        training_counts = Counter(record.training_run_id for record in records)
        training_names: dict[UUID | None, str] = {}
        for record in records:
            training_names.setdefault(record.training_run_id, record.model_display_name)

        recent_counts: dict[str, int] = defaultdict(int)
        for record in records:
            recent_counts[record.created_at.date().isoformat()] += 1

        return HistoryStatisticsResponse(
            total_saved_analyses=total,
            likely_real_count=real_count,
            likely_fake_count=fake_count,
            likely_real_percentage=self._percentage(real_count, total),
            likely_fake_percentage=self._percentage(fake_count, total),
            average_confidence=self._average(confidence_values),
            average_real_confidence=self._average(real_confidence_values),
            average_fake_confidence=self._average(fake_confidence_values),
            analyses_with_explanations=explained_count,
            analyses_without_explanations=total - explained_count,
            model_family_distribution=[
                HistoryDistributionItem(
                    name=name,
                    count=count,
                    percentage=self._percentage(count, total),
                )
                for name, count in sorted(family_counts.items())
            ],
            model_type_distribution=[
                HistoryDistributionItem(
                    name=name,
                    count=count,
                    percentage=self._percentage(count, total),
                )
                for name, count in sorted(type_counts.items())
            ],
            training_run_distribution=[
                TrainingRunHistoryItem(
                    training_run_id=training_run_id,
                    model_display_name=training_names.get(training_run_id, "Unknown model"),
                    count=count,
                    percentage=self._percentage(count, total),
                )
                for training_run_id, count in training_counts.most_common()
            ],
            recent_volume=[
                RecentHistoryVolumeItem(date=date, count=count)
                for date, count in sorted(recent_counts.items())
            ],
            interpretation=(
                "History analytics describe only articles analyzed and saved by this application; "
                "they are not claims about all news or about factual truth."
            ),
        )

    @staticmethod
    def _summary(record: AnalysisRecord) -> AnalysisHistorySummary:
        return AnalysisHistorySummary(
            id=record.id,
            training_run_id=record.training_run_id,
            model_family=ModelFamily(record.model_family),
            model_type=ClassicalModelType(record.model_type),
            model_name=record.model_name,
            model_display_name=record.model_display_name,
            title=record.title,
            article_preview=AnalysisHistoryService._preview(record.content),
            predicted_label=ArticleLabel(record.predicted_label),
            real_probability=record.real_probability,
            fake_probability=record.fake_probability,
            confidence=record.confidence,
            explanation_available=record.explanation_status == ExplanationStatus.GENERATED,
            explanation_method=record.explanation_method,
            review=AnalysisHistoryService._review_info(record, include_notes=False),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _detail(record: AnalysisRecord) -> AnalysisHistoryDetail:
        explanation = None
        if record.explanation_status == ExplanationStatus.GENERATED and record.explanation_generated_at:
            explanation = AnalysisExplanationDetail(
                explanation_method=record.explanation_method or "unknown",
                explained_class=ArticleLabel(record.explained_class or record.predicted_label),
                influences_toward_real=record.influences_toward_real,
                influences_toward_fake=record.influences_toward_fake,
                limitations=record.explanation_limitations,
                message=record.explanation_message,
                generated_at=record.explanation_generated_at,
            )
        return AnalysisHistoryDetail(
            id=record.id,
            training_run_id=record.training_run_id,
            model_family=ModelFamily(record.model_family),
            model_type=ClassicalModelType(record.model_type),
            model_name=record.model_name,
            model_display_name=record.model_display_name,
            title=record.title,
            content=record.content,
            text_composition_mode=record.text_composition_mode,
            predicted_label=ArticleLabel(record.predicted_label),
            real_probability=record.real_probability,
            fake_probability=record.fake_probability,
            confidence=record.confidence,
            probability_method=record.probability_method,
            explanation_status=record.explanation_status,
            explanation=explanation,
            review=AnalysisHistoryService._review_info(record, include_notes=True),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _review_info(record: AnalysisRecord, *, include_notes: bool) -> AnalysisReviewInfo:
        review = record.review
        if review is None:
            return AnalysisReviewInfo(status="unreviewed")
        return AnalysisReviewInfo(
            status="reviewed",
            review_id=review.id,
            verified_label=ArticleLabel(review.verified_label),
            is_prediction_correct=record.predicted_label == review.verified_label,
            reviewer_note=review.reviewer_note if include_notes else None,
            evidence_note=review.evidence_note if include_notes else None,
            reviewed_at=review.created_at,
            updated_at=review.updated_at,
        )

    @staticmethod
    def _preview(content: str | None, limit: int = 220) -> str | None:
        if not content:
            return None
        compact = " ".join(content.split())
        return compact if len(compact) <= limit else f"{compact[: limit - 3].rstrip()}..."

    @staticmethod
    def _percentage(value: int, total: int) -> float | None:
        if total == 0:
            return None
        return round((value / total) * 100, 2)

    @staticmethod
    def _average(values: list[float]) -> float | None:
        if not values:
            return None
        return round(sum(values) / len(values), 6)
