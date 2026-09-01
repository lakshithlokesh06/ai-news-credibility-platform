from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.evidence.service import EvidenceService
from app.models.analysis import AnalysisRecord
from app.models.article import ArticleLabel
from app.models.review import AnalysisReview, ReviewStatus
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, ModelLifecycleStatus
from app.repositories.training_run_repository import TrainingRunRepository
from app.review.repository import ReviewRepository, article_preview, has_explanation
from app.schemas.review import (
    AnalysisReviewInfo,
    CalibrationResponse,
    ConfusionMatrixResponse,
    DeleteReviewResponse,
    ErrorAnalysisItem,
    ErrorAnalysisResponse,
    ErrorConfidenceStatistics,
    PaginatedReviewQueueResponse,
    ProductionPerformanceResponse,
    ReliabilityBin,
    ReviewResponse,
    ReviewStatisticsResponse,
    ReviewUpsertRequest,
    RocAucResponse,
    TrainingRunReviewSummary,
)


class ReviewError(ValueError):
    def __init__(self, message: str, error_type: str = "review_error") -> None:
        super().__init__(message)
        self.error_type = error_type


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ReviewRepository(db)
        self.training_runs = TrainingRunRepository(db)

    def upsert_review(self, analysis_id: UUID, request: ReviewUpsertRequest) -> ReviewResponse:
        analysis = self._analysis_or_raise(analysis_id)
        review = analysis.review
        now = datetime.now(UTC)
        created = review is None
        if review is None:
            review = AnalysisReview(
                analysis_id=analysis.id,
                verified_label=request.verified_label.value,
                status=ReviewStatus.REVIEWED.value,
                reviewer_note=request.reviewer_note,
                evidence_note=request.evidence_note,
                created_at=now,
                updated_at=now,
            )
            self.repository.add_review(review)
        else:
            review.verified_label = request.verified_label.value
            review.status = ReviewStatus.REVIEWED.value
            review.reviewer_note = request.reviewer_note
            review.evidence_note = request.evidence_note
            review.updated_at = now
        self.db.commit()
        self.db.refresh(review)
        message = "Human review recorded." if created else "Human review updated."
        return ReviewResponse(analysis_id=analysis.id, review=self.review_info(analysis, review, include_notes=True), message=message)

    def delete_review(self, analysis_id: UUID) -> DeleteReviewResponse:
        self._analysis_or_raise(analysis_id)
        review = self.repository.get_review(analysis_id)
        if review is None:
            raise ReviewError("Analysis review was not found.", "review_not_found")
        self.repository.delete_review(review)
        self.db.commit()
        return DeleteReviewResponse(
            analysis_id=analysis_id,
            deleted=True,
            message="Human review removed. Prediction, explanation, and history content were retained.",
        )

    def queue(
        self,
        *,
        review_filter: str,
        predicted_label: ArticleLabel | None,
        model_family: ModelFamily | None,
        model_type: ClassicalModelType | None,
        training_run_id: UUID | None,
        confidence_bucket: str,
        search: str | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> PaginatedReviewQueueResponse:
        if training_run_id is not None:
            self._training_run_or_raise(training_run_id)
        items, total = self.repository.queue_records(
            review_filter=review_filter,
            predicted_label=predicted_label,
            model_family=model_family,
            model_type=model_type,
            training_run_id=training_run_id,
            confidence_bucket=confidence_bucket,
            high_confidence_threshold=settings.high_confidence_error_threshold,
            search=search,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        evidence_service = EvidenceService(self.db)
        return PaginatedReviewQueueResponse(
            items=[
                {
                    "id": record.id,
                    "training_run_id": record.training_run_id,
                    "model_family": ModelFamily(record.model_family),
                    "model_type": ClassicalModelType(record.model_type),
                    "model_name": record.model_name,
                    "model_display_name": record.model_display_name,
                    "title": record.title,
                    "article_preview": article_preview(record.content),
                    "predicted_label": ArticleLabel(record.predicted_label),
                    "confidence": record.confidence,
                    "explanation_available": has_explanation(record),
                    "review": self.review_info(record, record.review),
                    "evidence_summary": evidence_service.analysis_summary(record.id),
                    "created_at": record.created_at,
                }
                for record in items
            ],
            total=total,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    def statistics(self) -> ReviewStatisticsResponse:
        total_analyses, reviewed_rows, analysis_counts = self.repository.review_statistics()
        reviewed_count = len(reviewed_rows)
        reviewed_real = sum(1 for _record, review in reviewed_rows if review.verified_label == ArticleLabel.REAL.value)
        reviewed_fake = sum(1 for _record, review in reviewed_rows if review.verified_label == ArticleLabel.FAKE.value)
        correct = sum(1 for record, review in reviewed_rows if record.predicted_label == review.verified_label)
        incorrect = reviewed_count - correct

        per_run_reviewed: dict[UUID | None, list[tuple[AnalysisRecord, AnalysisReview]]] = defaultdict(list)
        for record, review in reviewed_rows:
            per_run_reviewed[record.training_run_id].append((record, review))
        analysis_count_map = dict(analysis_counts)
        training_run_ids = [run_id for run_id in analysis_count_map if run_id is not None]
        runs = {run.id: run for run in self.training_runs.list_by_ids(training_run_ids)}

        summaries = []
        for run_id, analysis_count in analysis_count_map.items():
            run = runs.get(run_id) if run_id is not None else None
            rows = per_run_reviewed.get(run_id, [])
            run_correct = sum(1 for record, review in rows if record.predicted_label == review.verified_label)
            summaries.append(
                TrainingRunReviewSummary(
                    training_run_id=run_id,
                    model_display_name=run.model_display_name if run else "Unknown model",
                    model_family=ModelFamily(run.model_family) if run else None,
                    model_type=ClassicalModelType(run.model_type) if run else None,
                    lifecycle_status=ModelLifecycleStatus(run.lifecycle_status) if run and run.lifecycle_status else None,
                    analysis_count=analysis_count,
                    reviewed_count=len(rows),
                    correct_count=run_correct,
                    incorrect_count=len(rows) - run_correct,
                    review_coverage_percentage=self._percentage(len(rows), analysis_count),
                    is_champion=bool(run and run.lifecycle_status == ModelLifecycleStatus.CHAMPION.value),
                )
            )

        summaries.sort(key=lambda item: (not item.is_champion, -item.reviewed_count, item.model_display_name))
        return ReviewStatisticsResponse(
            total_analyses=total_analyses,
            reviewed_analyses=reviewed_count,
            unreviewed_analyses=total_analyses - reviewed_count,
            review_coverage_percentage=self._percentage(reviewed_count, total_analyses),
            reviewed_real_count=reviewed_real,
            reviewed_fake_count=reviewed_fake,
            correct_prediction_count=correct,
            incorrect_prediction_count=incorrect,
            per_training_run=summaries,
            interpretation=(
                "Review coverage measures how many saved analyses have explicit human-verified labels. "
                "Accuracy and error metrics use only those reviewed records."
            ),
        )

    def performance(
        self,
        *,
        training_run_id: UUID | None,
        model_family: ModelFamily | None,
        created_after: datetime | None,
        created_before: datetime | None,
    ) -> ProductionPerformanceResponse:
        run = self._training_run_or_raise(training_run_id) if training_run_id else None
        rows = self.repository.reviewed_rows(
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
        )
        matrix = self._confusion(rows)
        reviewed_count = sum(sum(row) for row in matrix["matrix"])
        correct = matrix["true_real_pred_real"] + matrix["true_fake_pred_fake"]
        incorrect = reviewed_count - correct
        tp = matrix["true_fake_pred_fake"]
        fp = matrix["true_real_pred_fake"]
        fn = matrix["true_fake_pred_real"]
        precision = self._safe_divide(tp, tp + fp)
        recall = self._safe_divide(tp, tp + fn)
        f1 = None if precision is None or recall is None or precision + recall == 0 else round(2 * precision * recall / (precision + recall), 6)
        scope, display_name, family, model_type, test_metrics = self._scope_metadata(run, training_run_id)

        return ProductionPerformanceResponse(
            scope=scope,
            training_run_id=training_run_id,
            model_display_name=display_name,
            model_family=family,
            model_type=model_type,
            reviewed_count=reviewed_count,
            correct_count=correct,
            incorrect_count=incorrect,
            accuracy=self._safe_divide(correct, reviewed_count),
            precision=precision,
            recall=recall,
            f1=f1,
            roc_auc=self._roc_auc(rows),
            confusion_matrix=ConfusionMatrixResponse(**matrix),
            minimum_reviewed_samples=settings.performance_min_reviewed_samples,
            sufficiency_status=self._sufficiency(reviewed_count),
            held_out_test_metrics=test_metrics,
            limitations=self._performance_limitations(reviewed_count, training_run_id),
        )

    def calibration(
        self,
        *,
        training_run_id: UUID | None,
        model_family: ModelFamily | None,
        created_after: datetime | None,
        created_before: datetime | None,
        bins: int,
    ) -> CalibrationResponse:
        run = self._training_run_or_raise(training_run_id) if training_run_id else None
        rows = self.repository.reviewed_rows(
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
        )
        scoped = [(record, review) for record, review, _run in rows if record.confidence is not None]
        brier_values = []
        bucketed: dict[int, list[tuple[float, bool]]] = defaultdict(list)
        for record, review in scoped:
            confidence = float(record.confidence)
            correct = record.predicted_label == review.verified_label
            p_fake = self._fake_probability(record)
            if p_fake is not None:
                y_fake = 1.0 if review.verified_label == ArticleLabel.FAKE.value else 0.0
                brier_values.append((p_fake - y_fake) ** 2)
            index = min(int(confidence * bins), bins - 1)
            bucketed[index].append((confidence, correct))

        reliability_bins = []
        ece = 0.0
        total = len(scoped)
        for index in sorted(bucketed):
            values = bucketed[index]
            mean_confidence = sum(value for value, _correct in values) / len(values)
            observed_accuracy = sum(1 for _value, correct in values if correct) / len(values)
            if total:
                ece += (len(values) / total) * abs(mean_confidence - observed_accuracy)
            reliability_bins.append(
                ReliabilityBin(
                    lower_bound=round(index / bins, 6),
                    upper_bound=round((index + 1) / bins, 6),
                    sample_count=len(values),
                    mean_confidence=round(mean_confidence, 6),
                    observed_accuracy=round(observed_accuracy, 6),
                )
            )

        scope, display_name, _family, _model_type, _test_metrics = self._scope_metadata(run, training_run_id)
        limitations = ["Calibration diagnostics use only reviewed saved analyses and do not use training labels."]
        if total == 0:
            limitations.append("No reviewed analyses with confidence values are available for this scope.")
        elif total < settings.performance_min_reviewed_samples:
            limitations.append("Preliminary - the reviewed sample is below the configured minimum.")
        return CalibrationResponse(
            scope=scope,
            training_run_id=training_run_id,
            model_display_name=display_name,
            sample_count=total,
            bin_count=bins,
            brier_score=round(sum(brier_values) / len(brier_values), 6) if brier_values else None,
            expected_calibration_error=round(ece, 6) if total else None,
            reliability_bins=reliability_bins,
            minimum_reviewed_samples=settings.performance_min_reviewed_samples,
            sufficiency_status=self._sufficiency(total),
            limitations=limitations,
        )

    def errors(
        self,
        *,
        training_run_id: UUID | None,
        model_family: ModelFamily | None,
        error_type: str | None,
        min_confidence: float | None,
        max_confidence: float | None,
        created_after: datetime | None,
        created_before: datetime | None,
        limit: int,
        offset: int,
    ) -> ErrorAnalysisResponse:
        if training_run_id is not None:
            self._training_run_or_raise(training_run_id)
        rows, total = self.repository.error_rows(
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
        all_rows = self.repository.reviewed_rows(
            training_run_id=training_run_id,
            model_family=model_family,
            created_after=created_after,
            created_before=created_before,
        )
        return ErrorAnalysisResponse(
            items=[
                ErrorAnalysisItem(
                    analysis_id=record.id,
                    training_run_id=record.training_run_id,
                    model_display_name=run.model_display_name if run else record.model_display_name,
                    title=record.title,
                    article_preview=article_preview(record.content),
                    predicted_label=ArticleLabel(record.predicted_label),
                    verified_label=ArticleLabel(review.verified_label),
                    confidence=record.confidence,
                    error_type=self._error_type(record, review),
                    explanation_available=has_explanation(record),
                    created_at=record.created_at,
                    reviewed_at=review.updated_at,
                )
                for record, review, run in rows
            ],
            total=total,
            limit=limit,
            offset=offset,
            statistics=self._error_statistics(all_rows),
            definitions={
                "positive_class": "FAKE is treated as the positive class for precision, recall, F1, and false-positive/false-negative labels.",
                "false_positive": "Model predicted FAKE and the human-verified label is REAL.",
                "false_negative": "Model predicted REAL and the human-verified label is FAKE.",
                "high_confidence_model_errors": "Reviewed incorrect predictions with confidence at or above the configured high-confidence threshold.",
            },
        )

    def review_info(
        self,
        analysis: AnalysisRecord,
        review: AnalysisReview | None,
        *,
        include_notes: bool = False,
    ) -> AnalysisReviewInfo:
        if review is None:
            return AnalysisReviewInfo(status="unreviewed")
        return AnalysisReviewInfo(
            status="reviewed",
            review_id=review.id,
            verified_label=ArticleLabel(review.verified_label),
            is_prediction_correct=analysis.predicted_label == review.verified_label,
            reviewer_note=review.reviewer_note if include_notes else None,
            evidence_note=review.evidence_note if include_notes else None,
            reviewed_at=review.created_at,
            updated_at=review.updated_at,
        )

    def _analysis_or_raise(self, analysis_id: UUID) -> AnalysisRecord:
        analysis = self.repository.get_analysis(analysis_id)
        if analysis is None:
            raise ReviewError("Analysis record was not found.", "analysis_not_found")
        return analysis

    def _training_run_or_raise(self, training_run_id: UUID) -> MLTrainingRun:
        training_run = self.training_runs.get(training_run_id)
        if training_run is None:
            raise ReviewError("Training run was not found.", "training_run_not_found")
        return training_run

    def _scope_metadata(
        self,
        run: MLTrainingRun | None,
        training_run_id: UUID | None,
    ) -> tuple[str, str, ModelFamily | None, ClassicalModelType | None, dict | None]:
        if training_run_id is None:
            return "mixed_model_aggregate", "Mixed reviewed analyses", None, None, None
        if run is None:
            raise ReviewError("Training run was not found.", "training_run_not_found")
        return (
            "training_run",
            run.model_display_name,
            ModelFamily(run.model_family),
            ClassicalModelType(run.model_type),
            run.test_metrics,
        )

    @staticmethod
    def _confusion(rows: list[tuple[AnalysisRecord, AnalysisReview, MLTrainingRun | None]]) -> dict:
        true_real_pred_real = sum(
            1 for record, review, _run in rows
            if review.verified_label == ArticleLabel.REAL.value and record.predicted_label == ArticleLabel.REAL.value
        )
        true_real_pred_fake = sum(
            1 for record, review, _run in rows
            if review.verified_label == ArticleLabel.REAL.value and record.predicted_label == ArticleLabel.FAKE.value
        )
        true_fake_pred_real = sum(
            1 for record, review, _run in rows
            if review.verified_label == ArticleLabel.FAKE.value and record.predicted_label == ArticleLabel.REAL.value
        )
        true_fake_pred_fake = sum(
            1 for record, review, _run in rows
            if review.verified_label == ArticleLabel.FAKE.value and record.predicted_label == ArticleLabel.FAKE.value
        )
        return {
            "labels": [ArticleLabel.REAL, ArticleLabel.FAKE],
            "matrix": [
                [true_real_pred_real, true_real_pred_fake],
                [true_fake_pred_real, true_fake_pred_fake],
            ],
            "true_real_pred_real": true_real_pred_real,
            "true_real_pred_fake": true_real_pred_fake,
            "true_fake_pred_real": true_fake_pred_real,
            "true_fake_pred_fake": true_fake_pred_fake,
        }

    def _roc_auc(self, rows: list[tuple[AnalysisRecord, AnalysisReview, MLTrainingRun | None]]) -> RocAucResponse:
        pairs = []
        missing_probability = False
        for record, review, _run in rows:
            probability = self._fake_probability(record)
            if probability is None:
                missing_probability = True
                continue
            pairs.append((probability, review.verified_label == ArticleLabel.FAKE.value))
        positives = sum(1 for _probability, label in pairs if label)
        negatives = len(pairs) - positives
        if not pairs:
            return RocAucResponse(value=None, available=False, reason="No reviewed records have usable probabilities.")
        if missing_probability:
            return RocAucResponse(value=None, available=False, reason="Some reviewed records lack usable probabilities.")
        if positives == 0 or negatives == 0:
            return RocAucResponse(value=None, available=False, reason="Reviewed labels must include both REAL and FAKE.")

        sorted_pairs = sorted(pairs, key=lambda item: item[0])
        ranks = [0.0] * len(sorted_pairs)
        index = 0
        while index < len(sorted_pairs):
            end = index + 1
            while end < len(sorted_pairs) and sorted_pairs[end][0] == sorted_pairs[index][0]:
                end += 1
            average_rank = (index + 1 + end) / 2
            for rank_index in range(index, end):
                ranks[rank_index] = average_rank
            index = end
        positive_rank_sum = sum(rank for rank, (_probability, label) in zip(ranks, sorted_pairs, strict=True) if label)
        auc = (positive_rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
        return RocAucResponse(value=round(auc, 6), available=True, reason=None)

    @staticmethod
    def _fake_probability(record: AnalysisRecord) -> float | None:
        if record.fake_probability is not None:
            return float(record.fake_probability)
        if record.confidence is None:
            return None
        return float(record.confidence) if record.predicted_label == ArticleLabel.FAKE.value else 1.0 - float(record.confidence)

    def _error_statistics(self, rows: list[tuple[AnalysisRecord, AnalysisReview, MLTrainingRun | None]]) -> ErrorConfidenceStatistics:
        correct = [record.confidence for record, review, _run in rows if record.predicted_label == review.verified_label and record.confidence is not None]
        incorrect = [record.confidence for record, review, _run in rows if record.predicted_label != review.verified_label and record.confidence is not None]
        high_threshold = settings.high_confidence_error_threshold
        low_threshold = 0.60
        high_confidence_total = [record for record, _review, _run in rows if record.confidence is not None and record.confidence >= high_threshold]
        low_confidence_total = [record for record, _review, _run in rows if record.confidence is not None and record.confidence < low_threshold]
        high_errors = [
            record for record, review, _run in rows
            if record.confidence is not None and record.confidence >= high_threshold and record.predicted_label != review.verified_label
        ]
        low_errors = [
            record for record, review, _run in rows
            if record.confidence is not None and record.confidence < low_threshold and record.predicted_label != review.verified_label
        ]
        return ErrorConfidenceStatistics(
            average_confidence_correct=self._average(correct),
            average_confidence_incorrect=self._average(incorrect),
            high_confidence_error_count=len(high_errors),
            high_confidence_error_rate=self._safe_divide(len(high_errors), len(high_confidence_total)),
            low_confidence_error_count=len(low_errors),
            low_confidence_error_rate=self._safe_divide(len(low_errors), len(low_confidence_total)),
            high_confidence_threshold=high_threshold,
            low_confidence_threshold=low_threshold,
        )

    @staticmethod
    def _error_type(record: AnalysisRecord, review: AnalysisReview) -> str:
        if record.predicted_label == ArticleLabel.FAKE.value and review.verified_label == ArticleLabel.REAL.value:
            return "false_positive"
        if record.predicted_label == ArticleLabel.REAL.value and review.verified_label == ArticleLabel.FAKE.value:
            return "false_negative"
        if record.predicted_label == ArticleLabel.REAL.value and review.verified_label == ArticleLabel.REAL.value:
            return "correct_real"
        return "correct_fake"

    @staticmethod
    def _performance_limitations(reviewed_count: int, training_run_id: UUID | None) -> list[str]:
        limitations = [
            "Reviewed production-style metrics use only saved analyses with explicit human-verified labels.",
            "Held-out test metrics are calculated during training and are reported separately.",
        ]
        if training_run_id is None:
            limitations.append("This is a mixed-model aggregate and should not be used to judge one specific model.")
        if reviewed_count == 0:
            limitations.append("No reviewed records are available for this scope.")
        elif reviewed_count < settings.performance_min_reviewed_samples:
            limitations.append("Preliminary - the reviewed sample is below the configured minimum.")
        return limitations

    @staticmethod
    def _sufficiency(sample_count: int) -> str:
        if sample_count == 0:
            return "insufficient_data"
        if sample_count < settings.performance_min_reviewed_samples:
            return "preliminary"
        return "sufficient"

    @staticmethod
    def _safe_divide(numerator: int | float, denominator: int | float) -> float | None:
        if denominator == 0:
            return None
        return round(numerator / denominator, 6)

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
