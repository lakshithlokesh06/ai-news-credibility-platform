from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis import AnalysisRecord
from app.models.evidence import AnalysisClaim, ClaimEvidence
from app.models.training import ModelFamily


class EvidenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_analysis(self, analysis_id: UUID) -> AnalysisRecord | None:
        return self.db.get(AnalysisRecord, analysis_id)

    def get_claim(self, claim_id: UUID) -> AnalysisClaim | None:
        return self.db.execute(
            select(AnalysisClaim)
            .options(selectinload(AnalysisClaim.evidence_items))
            .where(AnalysisClaim.id == claim_id)
        ).scalars().first()

    def get_evidence(self, evidence_id: UUID) -> ClaimEvidence | None:
        return self.db.execute(
            select(ClaimEvidence)
            .options(selectinload(ClaimEvidence.claim))
            .where(ClaimEvidence.id == evidence_id)
        ).scalars().first()

    def add_claim(self, claim: AnalysisClaim) -> AnalysisClaim:
        self.db.add(claim)
        return claim

    def add_evidence(self, evidence: ClaimEvidence) -> ClaimEvidence:
        self.db.add(evidence)
        return evidence

    def delete_claim(self, claim: AnalysisClaim) -> None:
        self.db.delete(claim)

    def delete_evidence(self, evidence: ClaimEvidence) -> None:
        self.db.delete(evidence)

    def list_claims(
        self,
        *,
        analysis_id: UUID,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AnalysisClaim], int]:
        statement = (
            select(AnalysisClaim)
            .options(selectinload(AnalysisClaim.evidence_items))
            .where(AnalysisClaim.analysis_id == analysis_id)
        )
        count_statement = select(func.count()).select_from(AnalysisClaim).where(AnalysisClaim.analysis_id == analysis_id)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(AnalysisClaim.claim_text.ilike(pattern))
            count_statement = count_statement.where(AnalysisClaim.claim_text.ilike(pattern))
        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(
            statement.order_by(AnalysisClaim.created_at.desc()).limit(limit).offset(offset)
        ).scalars().all()
        return list(items), int(total)

    def duplicate_evidence(
        self,
        *,
        claim_id: UUID,
        normalized_source_url: str,
        exclude_evidence_id: UUID | None = None,
    ) -> ClaimEvidence | None:
        statement = select(ClaimEvidence).where(
            ClaimEvidence.claim_id == claim_id,
            ClaimEvidence.normalized_source_url == normalized_source_url,
        )
        if exclude_evidence_id is not None:
            statement = statement.where(ClaimEvidence.id != exclude_evidence_id)
        return self.db.execute(statement).scalars().first()

    def claims_for_analysis_summary(self, analysis_id: UUID) -> list[AnalysisClaim]:
        return list(
            self.db.execute(
                select(AnalysisClaim)
                .options(selectinload(AnalysisClaim.evidence_items))
                .where(AnalysisClaim.analysis_id == analysis_id)
            ).scalars().all()
        )

    def claims_for_analysis_summaries(self, analysis_ids: list[UUID]) -> list[AnalysisClaim]:
        if not analysis_ids:
            return []
        return list(
            self.db.execute(
                select(AnalysisClaim)
                .options(selectinload(AnalysisClaim.evidence_items))
                .where(AnalysisClaim.analysis_id.in_(analysis_ids))
            ).scalars().all()
        )

    def statistics_rows(
        self,
        *,
        training_run_id: UUID | None = None,
        model_family: ModelFamily | None = None,
        search: str | None = None,
    ) -> list[AnalysisClaim]:
        statement = (
            select(AnalysisClaim)
            .join(AnalysisRecord, AnalysisRecord.id == AnalysisClaim.analysis_id)
            .options(selectinload(AnalysisClaim.evidence_items))
        )
        if training_run_id is not None:
            statement = statement.where(AnalysisRecord.training_run_id == training_run_id)
        if model_family is not None:
            statement = statement.where(AnalysisRecord.model_family == model_family.value)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.outerjoin(ClaimEvidence).where(
                or_(
                    AnalysisClaim.claim_text.ilike(pattern),
                    ClaimEvidence.source_title.ilike(pattern),
                    ClaimEvidence.publisher.ilike(pattern),
                )
            )
        return list(self.db.execute(statement).unique().scalars().all())
