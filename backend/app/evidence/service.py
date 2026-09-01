from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import UUID

from sqlalchemy.orm import Session

from app.evidence.repository import EvidenceRepository
from app.models.evidence import AnalysisClaim, ClaimEvidence, EvidenceAssessment
from app.models.training import ModelFamily
from app.schemas.evidence import (
    AnalysisEvidenceSummary,
    ClaimCreate,
    ClaimEvidenceCounts,
    ClaimResponse,
    ClaimsListResponse,
    ClaimUpdate,
    DeleteClaimResponse,
    DeleteEvidenceResponse,
    EvidenceCreate,
    EvidenceResponse,
    EvidenceStatisticsResponse,
    EvidenceUpdate,
)


class EvidenceError(ValueError):
    def __init__(self, message: str, error_type: str = "evidence_error") -> None:
        super().__init__(message)
        self.error_type = error_type


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = EvidenceRepository(db)

    def create_claim(self, analysis_id: UUID, request: ClaimCreate) -> ClaimResponse:
        analysis = self.repository.get_analysis(analysis_id)
        if analysis is None:
            raise EvidenceError("Analysis record was not found.", "analysis_not_found")
        self._validate_offsets(
            article_text=self._article_text(analysis.title, analysis.content),
            claim_text=request.claim_text,
            start_offset=request.start_offset,
            end_offset=request.end_offset,
        )
        now = datetime.now(UTC)
        claim = AnalysisClaim(
            analysis_id=analysis.id,
            claim_text=request.claim_text,
            start_offset=request.start_offset,
            end_offset=request.end_offset,
            status=request.status,
            reviewer_note=request.reviewer_note,
            created_at=now,
            updated_at=now,
        )
        self.repository.add_claim(claim)
        self.db.commit()
        self.db.refresh(claim)
        return self.claim_response(claim)

    def list_claims(self, analysis_id: UUID, *, search: str | None, limit: int, offset: int) -> ClaimsListResponse:
        if self.repository.get_analysis(analysis_id) is None:
            raise EvidenceError("Analysis record was not found.", "analysis_not_found")
        claims, total = self.repository.list_claims(analysis_id=analysis_id, search=search, limit=limit, offset=offset)
        return ClaimsListResponse(
            items=[self.claim_response(claim) for claim in claims],
            total=total,
            limit=limit,
            offset=offset,
        )

    def update_claim(self, claim_id: UUID, request: ClaimUpdate) -> ClaimResponse:
        claim = self._claim_or_raise(claim_id)
        analysis = self.repository.get_analysis(claim.analysis_id)
        if analysis is None:
            raise EvidenceError("Analysis record was not found.", "analysis_not_found")
        next_claim_text = request.claim_text if request.claim_text is not None else claim.claim_text
        offsets_requested = "start_offset" in request.model_fields_set or "end_offset" in request.model_fields_set
        next_start = request.start_offset if offsets_requested else claim.start_offset
        next_end = request.end_offset if offsets_requested else claim.end_offset
        self._validate_offsets(
            article_text=self._article_text(analysis.title, analysis.content),
            claim_text=next_claim_text,
            start_offset=next_start,
            end_offset=next_end,
        )
        claim.claim_text = next_claim_text
        claim.start_offset = next_start
        claim.end_offset = next_end
        if request.status is not None:
            claim.status = request.status
        if "reviewer_note" in request.model_fields_set:
            claim.reviewer_note = request.reviewer_note
        claim.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(claim)
        return self.claim_response(claim)

    def delete_claim(self, claim_id: UUID) -> DeleteClaimResponse:
        claim = self._claim_or_raise(claim_id)
        removed_evidence_count = len(claim.evidence_items)
        self.repository.delete_claim(claim)
        self.db.commit()
        return DeleteClaimResponse(
            claim_id=claim_id,
            deleted=True,
            removed_evidence_count=removed_evidence_count,
            message="Claim deleted. Associated evidence references were removed; the saved analysis and human review were retained.",
        )

    def create_evidence(self, claim_id: UUID, request: EvidenceCreate) -> EvidenceResponse:
        claim = self._claim_or_raise(claim_id)
        normalized_url = self.normalize_url(request.source_url)
        if self.repository.duplicate_evidence(claim_id=claim.id, normalized_source_url=normalized_url):
            raise EvidenceError("This evidence URL is already recorded for the claim.", "duplicate_evidence")
        now = datetime.now(UTC)
        evidence = ClaimEvidence(
            claim_id=claim.id,
            source_url=request.source_url,
            normalized_source_url=normalized_url,
            source_title=request.source_title,
            publisher=request.publisher,
            publication_date=request.publication_date,
            assessment=request.assessment,
            evidence_excerpt=request.evidence_excerpt,
            reviewer_note=request.reviewer_note,
            created_at=now,
            updated_at=now,
        )
        self.repository.add_evidence(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return self.evidence_response(evidence)

    def update_evidence(self, evidence_id: UUID, request: EvidenceUpdate) -> EvidenceResponse:
        evidence = self._evidence_or_raise(evidence_id)
        if request.source_url is not None:
            normalized_url = self.normalize_url(request.source_url)
            if self.repository.duplicate_evidence(
                claim_id=evidence.claim_id,
                normalized_source_url=normalized_url,
                exclude_evidence_id=evidence.id,
            ):
                raise EvidenceError("This evidence URL is already recorded for the claim.", "duplicate_evidence")
            evidence.source_url = request.source_url
            evidence.normalized_source_url = normalized_url
        if "source_title" in request.model_fields_set:
            evidence.source_title = request.source_title
        if "publisher" in request.model_fields_set:
            evidence.publisher = request.publisher
        if request.assessment is not None:
            evidence.assessment = request.assessment
        if "publication_date" in request.model_fields_set:
            evidence.publication_date = request.publication_date
        if "evidence_excerpt" in request.model_fields_set:
            evidence.evidence_excerpt = request.evidence_excerpt
        if "reviewer_note" in request.model_fields_set:
            evidence.reviewer_note = request.reviewer_note
        evidence.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(evidence)
        return self.evidence_response(evidence)

    def delete_evidence(self, evidence_id: UUID) -> DeleteEvidenceResponse:
        evidence = self._evidence_or_raise(evidence_id)
        self.repository.delete_evidence(evidence)
        self.db.commit()
        return DeleteEvidenceResponse(
            evidence_id=evidence_id,
            deleted=True,
            message="Evidence reference deleted. The claim, saved analysis, and human review were retained.",
        )

    def analysis_summary(self, analysis_id: UUID) -> AnalysisEvidenceSummary:
        if self.repository.get_analysis(analysis_id) is None:
            raise EvidenceError("Analysis record was not found.", "analysis_not_found")
        claims = self.repository.claims_for_analysis_summary(analysis_id)
        return self._summary_from_claims(analysis_id, claims)

    def statistics(
        self,
        *,
        training_run_id: UUID | None = None,
        model_family: ModelFamily | None = None,
        search: str | None = None,
    ) -> EvidenceStatisticsResponse:
        claims = self.repository.statistics_rows(
            training_run_id=training_run_id,
            model_family=model_family,
            search=search,
        )
        evidence_counts = self._assessment_counts(evidence for claim in claims for evidence in claim.evidence_items)
        claims_with_evidence = sum(1 for claim in claims if claim.evidence_items)
        return EvidenceStatisticsResponse(
            analyses_with_claims=len({claim.analysis_id for claim in claims}),
            total_claims=len(claims),
            total_evidence_records=sum(len(claim.evidence_items) for claim in claims),
            claims_with_evidence=claims_with_evidence,
            claims_without_evidence=len(claims) - claims_with_evidence,
            evidence_coverage_percentage=self._percentage(claims_with_evidence, len(claims)),
            assessment_distribution={
                key: value for key, value in evidence_counts.items() if key != "total"
            },
            latest_evidence_updated_at=self._latest_evidence_updated_at(claims),
            interpretation=(
                "Evidence statistics describe manual review workflow coverage only. "
                "They are not credibility scores and do not affect verified labels or model performance metrics."
            ),
        )

    def claim_response(self, claim: AnalysisClaim) -> ClaimResponse:
        return ClaimResponse(
            id=claim.id,
            analysis_id=claim.analysis_id,
            claim_text=claim.claim_text,
            start_offset=claim.start_offset,
            end_offset=claim.end_offset,
            status=claim.status,
            reviewer_note=claim.reviewer_note,
            evidence_counts=ClaimEvidenceCounts(**self._assessment_counts(claim.evidence_items)),
            evidence=[self.evidence_response(evidence) for evidence in claim.evidence_items],
            created_at=claim.created_at,
            updated_at=claim.updated_at,
        )

    @staticmethod
    def evidence_response(evidence: ClaimEvidence) -> EvidenceResponse:
        return EvidenceResponse(
            id=evidence.id,
            claim_id=evidence.claim_id,
            source_url=evidence.source_url,
            source_title=evidence.source_title,
            publisher=evidence.publisher,
            publication_date=evidence.publication_date,
            assessment=evidence.assessment,
            evidence_excerpt=evidence.evidence_excerpt,
            reviewer_note=evidence.reviewer_note,
            created_at=evidence.created_at,
            updated_at=evidence.updated_at,
        )

    @classmethod
    def normalize_url(cls, value: str) -> str:
        parsed = urlparse(value.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise EvidenceError("Evidence URL must use http or https.", "invalid_evidence_url")
        query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)), doseq=True)
        path = parsed.path.rstrip("/") or "/"
        return urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                path,
                "",
                query,
                "",
            )
        )

    def _summary_from_claims(self, analysis_id: UUID, claims: list[AnalysisClaim]) -> AnalysisEvidenceSummary:
        evidence_items = [evidence for claim in claims for evidence in claim.evidence_items]
        counts = self._assessment_counts(evidence_items)
        claims_with_evidence = sum(1 for claim in claims if claim.evidence_items)
        return AnalysisEvidenceSummary(
            analysis_id=analysis_id,
            total_claims=len(claims),
            claims_with_evidence=claims_with_evidence,
            claims_without_evidence=len(claims) - claims_with_evidence,
            total_evidence_references=len(evidence_items),
            supporting_evidence_count=counts["supports"],
            contradicting_evidence_count=counts["contradicts"],
            neutral_evidence_count=counts["neutral"],
            unclear_evidence_count=counts["unclear"],
            evidence_coverage_percentage=self._percentage(claims_with_evidence, len(claims)),
            latest_evidence_updated_at=self._latest_evidence_updated_at(claims),
            interpretation=(
                "Evidence coverage is a workflow metric. Evidence assessments do not automatically determine the human-verified label."
            ),
        )

    @staticmethod
    def _assessment_counts(evidence_items) -> dict[str, int]:
        counts = {assessment.value: 0 for assessment in EvidenceAssessment}
        for evidence in evidence_items:
            counts[evidence.assessment] += 1
        counts["total"] = sum(counts.values())
        return counts

    @staticmethod
    def _latest_evidence_updated_at(claims: list[AnalysisClaim]) -> datetime | None:
        updated_at_values = [
            evidence.updated_at
            for claim in claims
            for evidence in claim.evidence_items
            if evidence.updated_at is not None
        ]
        if not updated_at_values:
            return None
        return max(updated_at_values)

    def _claim_or_raise(self, claim_id: UUID) -> AnalysisClaim:
        claim = self.repository.get_claim(claim_id)
        if claim is None:
            raise EvidenceError("Claim was not found.", "claim_not_found")
        return claim

    def _evidence_or_raise(self, evidence_id: UUID) -> ClaimEvidence:
        evidence = self.repository.get_evidence(evidence_id)
        if evidence is None:
            raise EvidenceError("Evidence reference was not found.", "evidence_not_found")
        return evidence

    @staticmethod
    def _article_text(title: str | None, content: str | None) -> str:
        return "\n\n".join(part for part in [title, content] if part)

    @staticmethod
    def _validate_offsets(
        *,
        article_text: str,
        claim_text: str,
        start_offset: int | None,
        end_offset: int | None,
    ) -> None:
        if start_offset is None and end_offset is None:
            return
        if start_offset is None or end_offset is None or end_offset <= start_offset:
            raise EvidenceError("Claim offsets are invalid.", "invalid_claim_offsets")
        if end_offset > len(article_text):
            raise EvidenceError("Claim offsets exceed the saved article text length.", "invalid_claim_offsets")
        selected = " ".join(article_text[start_offset:end_offset].split()).lower()
        normalized_claim = " ".join(claim_text.split()).lower()
        if selected and normalized_claim and selected not in normalized_claim and normalized_claim not in selected:
            raise EvidenceError("Claim text does not reasonably match the selected article span.", "claim_offset_mismatch")

    @staticmethod
    def _percentage(value: int, total: int) -> float | None:
        if total == 0:
            return None
        return round((value / total) * 100, 2)
