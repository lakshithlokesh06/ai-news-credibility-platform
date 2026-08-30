from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.monitoring import ModelMonitoringProfile
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, TrainingRunStatus
from app.monitoring.config import DEFAULT_MONITORING_CONFIG, MONITORING_LIMITATIONS, PROFILE_VERSION, MonitoringError
from app.monitoring.current_profile import build_current_profile
from app.monitoring.drift_metrics import classify_metric, jensen_shannon_divergence, ks_statistic, population_stability_index
from app.monitoring.profile_generation import build_reference_profile
from app.monitoring.status import aggregate_input_status, overall_status
from app.repositories.monitoring_repository import MonitoringProfileRepository
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.monitoring import (
    ConfidenceMonitoring,
    ModelMonitoringResponse,
    MonitoringConfig,
    MonitoringMetric,
    MonitoringOverviewItem,
    MonitoringOverviewResponse,
    MonitoringProfileResponse,
    UsageMonitoring,
)
from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig


class MonitoringService:
    def __init__(self, db: Session, artifact_base_dir: Path | None = None) -> None:
        self.db = db
        self.artifact_base_dir = artifact_base_dir
        self.training_runs = TrainingRunRepository(db)
        self.profiles = MonitoringProfileRepository(db)

    def generate_reference_profile(self, training_run_id: UUID, *, refresh: bool = True) -> ModelMonitoringProfile:
        training_run = self._completed_training_run(training_run_id)
        if not refresh:
            existing = self.profiles.get_active(training_run_id)
            if existing is not None:
                return existing
        payload = build_reference_profile(self.db, training_run, artifact_base_dir=self.artifact_base_dir)
        now = datetime.now(UTC)
        profile = self.profiles.save_or_update(
            training_run_id=training_run.id,
            profile_version=PROFILE_VERSION,
            sample_count=payload["sample_count"],
            reference_statistics=payload["reference_statistics"],
            reference_label_distribution=payload["reference_label_distribution"],
            feature_metadata=payload["feature_metadata"],
            now=now,
        )
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def monitor_model(
        self,
        training_run_id: UUID,
        config: MonitoringConfig | None = None,
    ) -> ModelMonitoringResponse:
        config = config or DEFAULT_MONITORING_CONFIG
        training_run = self._completed_training_run(training_run_id)
        profile = self.profiles.get_active(training_run_id)
        window_records = self._latest_records(training_run_id, config.window_size)
        all_counts = self._usage_counts(training_run_id)
        current = build_current_profile(
            window_records,
            model_family=training_run.model_family,
            composition_config=TextCompositionConfig(**(training_run.text_composition_config or {})),
            preprocessing_config=PreprocessingConfig(**(training_run.preprocessing_config or {})),
        )
        has_profile = profile is not None
        has_enough_data = len(window_records) >= config.minimum_sample_count

        input_metrics = self._input_drift_metrics(profile, current, config) if profile and has_enough_data else []
        prediction_metric = self._prediction_drift_metric(profile, current, config) if profile and has_enough_data else self._unavailable_metric(
            "prediction_distribution_js_divergence",
            "Prediction distribution drift is unavailable until a reference profile and enough saved analyses exist.",
        )
        confidence_metrics = self._confidence_metrics(profile, current, config, has_enough_data)
        status, reasons = overall_status(input_metrics + [prediction_metric, confidence_metrics.confidence_shift], has_enough_data=has_enough_data, has_profile=has_profile)

        return ModelMonitoringResponse(
            training_run_id=training_run.id,
            model_display_name=training_run.model_display_name,
            model_family=ModelFamily(training_run.model_family),
            model_type=ClassicalModelType(training_run.model_type),
            model_name=training_run.base_model_name,
            monitoring_window={"window_size": config.window_size, "minimum_sample_count": config.minimum_sample_count},
            reference_profile_status="available" if profile else "missing",
            reference_profile=MonitoringProfileResponse.model_validate(profile) if profile else None,
            sample_counts={
                "reference": profile.sample_count if profile else 0,
                "current_window": len(window_records),
                "total_saved_analyses_for_model": all_counts["total"],
            },
            input_drift_metrics=input_metrics,
            prediction_drift=prediction_metric,
            confidence_metrics=confidence_metrics,
            usage_metrics=self._usage_metrics(current, all_counts, len(window_records)),
            overall_status=status,
            status_reasons=reasons,
            limitations=MONITORING_LIMITATIONS,
        )

    def overview(self, config: MonitoringConfig | None = None) -> MonitoringOverviewResponse:
        config = config or DEFAULT_MONITORING_CONFIG
        runs, _total = self.training_runs.list_runs(status=TrainingRunStatus.COMPLETED, limit=100, offset=0)
        items = []
        for run in runs:
            try:
                detail = self.monitor_model(run.id, config)
            except MonitoringError:
                continue
            items.append(
                MonitoringOverviewItem(
                    training_run_id=detail.training_run_id,
                    model_display_name=detail.model_display_name,
                    model_family=detail.model_family,
                    model_type=detail.model_type,
                    model_name=detail.model_name,
                    recent_analysis_count=detail.usage_metrics.analyses_in_window,
                    monitoring_status=detail.overall_status,
                    prediction_drift_status=detail.prediction_drift.status,
                    input_drift_status=aggregate_input_status(detail.input_drift_metrics),
                    average_confidence=detail.usage_metrics.average_confidence,
                    last_analyzed_at=detail.usage_metrics.last_used_at,
                )
            )

        return MonitoringOverviewResponse(
            items=items,
            total_completed_models=len(items),
            healthy_models=sum(1 for item in items if item.monitoring_status == "healthy"),
            models_needing_attention=sum(1 for item in items if item.monitoring_status in {"watch", "drift_detected"}),
            insufficient_data_models=sum(1 for item in items if item.monitoring_status == "insufficient_data"),
            recent_analyses=sum(item.recent_analysis_count for item in items),
            limitations=MONITORING_LIMITATIONS,
        )

    def _completed_training_run(self, training_run_id: UUID) -> MLTrainingRun:
        training_run = self.training_runs.get(training_run_id)
        if training_run is None:
            raise MonitoringError("Training run was not found.", "missing_training_run")
        if training_run.status != TrainingRunStatus.COMPLETED.value:
            raise MonitoringError("Only completed training runs can be monitored.", "incomplete_training_run")
        return training_run

    def _latest_records(self, training_run_id: UUID, limit: int) -> list[AnalysisRecord]:
        return list(
            self.db.execute(
                select(AnalysisRecord)
                .where(AnalysisRecord.training_run_id == training_run_id)
                .order_by(AnalysisRecord.created_at.desc())
                .limit(limit)
            ).scalars().all()
        )

    def _usage_counts(self, training_run_id: UUID) -> dict:
        total, real, fake, explained, average_confidence, last_used_at = self.db.execute(
            select(
                func.count(AnalysisRecord.id),
                func.sum(case((AnalysisRecord.predicted_label == "REAL", 1), else_=0)),
                func.sum(case((AnalysisRecord.predicted_label == "FAKE", 1), else_=0)),
                func.sum(case((AnalysisRecord.explanation_status == ExplanationStatus.GENERATED, 1), else_=0)),
                func.avg(AnalysisRecord.confidence),
                func.max(AnalysisRecord.created_at),
            ).where(AnalysisRecord.training_run_id == training_run_id)
        ).one()
        return {
            "total": int(total or 0),
            "real": int(real or 0),
            "fake": int(fake or 0),
            "explained": int(explained or 0),
            "average_confidence": round(float(average_confidence), 6) if average_confidence is not None else None,
            "last_used_at": last_used_at,
        }

    def _input_drift_metrics(self, profile: ModelMonitoringProfile | None, current: dict, config: MonitoringConfig) -> list[MonitoringMetric]:
        if profile is None:
            return []
        reference = profile.reference_statistics
        metrics = [
            self._metric(
                "text_length_psi",
                population_stability_index(
                    reference.get("text_length_distribution", []),
                    current["text_length_distribution"],
                ),
                config.psi_warning_threshold,
                config.psi_drift_threshold,
                "Text length distribution compared with the model reference profile.",
            ),
            self._metric(
                "title_length_psi",
                population_stability_index(
                    reference.get("title_length_distribution", []),
                    current["title_length_distribution"],
                ),
                config.psi_warning_threshold,
                config.psi_drift_threshold,
                "Title length distribution compared with the model reference profile.",
            ),
            self._metric(
                "text_length_ks_statistic",
                ks_statistic(reference.get("reference_text_lengths", []), current["text_lengths"]),
                config.ks_warning_threshold,
                config.ks_drift_threshold,
                "Kolmogorov-Smirnov statistic for reference versus current text lengths.",
            ),
        ]
        return metrics

    def _prediction_drift_metric(self, profile: ModelMonitoringProfile | None, current: dict, config: MonitoringConfig) -> MonitoringMetric:
        if profile is None:
            return self._unavailable_metric(
                "prediction_distribution_js_divergence",
                "Prediction distribution drift is unavailable without a reference profile.",
            )
        reference = profile.reference_label_distribution
        value = jensen_shannon_divergence(
            [int(reference.get("REAL", 0)), int(reference.get("FAKE", 0))],
            [
                int(current["prediction_distribution"].get("REAL", 0)),
                int(current["prediction_distribution"].get("FAKE", 0)),
            ],
        )
        return self._metric(
            "prediction_distribution_js_divergence",
            value,
            config.js_warning_threshold,
            config.js_drift_threshold,
            "Prediction distribution compared with the model's training-label distribution.",
        )

    def _confidence_metrics(
        self,
        profile: ModelMonitoringProfile | None,
        current: dict,
        config: MonitoringConfig,
        has_enough_data: bool,
    ) -> ConfidenceMonitoring:
        confidences = current["confidence_values"]
        total = len(confidences)
        if not has_enough_data or total == 0:
            shift = self._unavailable_metric(
                "confidence_distribution_psi",
                "Confidence monitoring is unavailable until enough saved analyses with confidence values exist.",
            )
        elif profile and profile.reference_statistics.get("confidence_distribution"):
            shift = self._metric(
                "confidence_distribution_psi",
                population_stability_index(
                    profile.reference_statistics["confidence_distribution"],
                    current["confidence_distribution"],
                ),
                config.psi_warning_threshold,
                config.psi_drift_threshold,
                "Confidence distribution compared with a stored reference confidence distribution.",
            )
        else:
            shift = self._unavailable_metric(
                "confidence_distribution_psi",
                "No legitimate training/validation confidence reference is stored for this model.",
            )

        return ConfidenceMonitoring(
            average_confidence=current["average_confidence"],
            median_confidence=current["median_confidence"],
            low_confidence_rate=_percentage(
                sum(1 for value in confidences if value < config.low_confidence_threshold),
                total,
            ),
            high_confidence_rate=_percentage(
                sum(1 for value in confidences if value >= config.high_confidence_threshold),
                total,
            ),
            average_real_probability=current["average_real_probability"],
            average_fake_probability=current["average_fake_probability"],
            confidence_distribution=current["confidence_distribution"],
            confidence_shift=shift,
        )

    def _usage_metrics(self, current: dict, all_counts: dict, window_count: int) -> UsageMonitoring:
        total = all_counts["total"]
        return UsageMonitoring(
            total_analyses=total,
            analyses_in_window=window_count,
            real_prediction_count=all_counts["real"],
            fake_prediction_count=all_counts["fake"],
            explanation_generation_rate=_percentage(all_counts["explained"], total),
            average_confidence=all_counts["average_confidence"],
            last_used_at=all_counts["last_used_at"],
            recent_volume=current["recent_volume"],
        )

    @staticmethod
    def _metric(metric_name: str, value: float | None, warning: float, drift: float, interpretation: str) -> MonitoringMetric:
        return MonitoringMetric(
            metric_name=metric_name,
            metric_value=value,
            warning_threshold=warning,
            drift_threshold=drift,
            status=classify_metric(value, warning, drift),
            interpretation=interpretation,
        )

    @staticmethod
    def _unavailable_metric(metric_name: str, interpretation: str) -> MonitoringMetric:
        return MonitoringMetric(
            metric_name=metric_name,
            metric_value=None,
            warning_threshold=None,
            drift_threshold=None,
            status="insufficient_data",
            interpretation=interpretation,
        )


def _percentage(value: int, total: int) -> float | None:
    if total == 0:
        return None
    return round(float(value / total), 6)
