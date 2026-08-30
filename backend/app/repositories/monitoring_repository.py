from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monitoring import ModelMonitoringProfile, MonitoringProfileStatus


class MonitoringProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active(self, training_run_id: UUID) -> ModelMonitoringProfile | None:
        return self.db.execute(
            select(ModelMonitoringProfile).where(
                ModelMonitoringProfile.training_run_id == training_run_id,
                ModelMonitoringProfile.status == MonitoringProfileStatus.ACTIVE,
            )
        ).scalar_one_or_none()

    def save_or_update(
        self,
        *,
        training_run_id: UUID,
        profile_version: str,
        sample_count: int,
        reference_statistics: dict,
        reference_label_distribution: dict,
        feature_metadata: dict,
        now,
    ) -> ModelMonitoringProfile:
        profile = self.get_active(training_run_id)
        if profile is None:
            profile = ModelMonitoringProfile(
                training_run_id=training_run_id,
                profile_version=profile_version,
                status=MonitoringProfileStatus.ACTIVE,
                sample_count=sample_count,
                reference_statistics=reference_statistics,
                reference_label_distribution=reference_label_distribution,
                feature_metadata=feature_metadata,
                created_at=now,
                updated_at=now,
            )
            self.db.add(profile)
        else:
            profile.sample_count = sample_count
            profile.reference_statistics = reference_statistics
            profile.reference_label_distribution = reference_label_distribution
            profile.feature_metadata = feature_metadata
            profile.updated_at = now
        return profile
