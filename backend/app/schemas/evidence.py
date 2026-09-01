from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings

ClaimStatusValue = Literal["open", "reviewed"]
EvidenceAssessmentValue = Literal["supports", "contradicts", "neutral", "unclear"]


class ClaimBase(BaseModel):
    claim_text: str = Field(min_length=settings.claim_text_min_chars, max_length=settings.claim_text_max_chars)
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, gt=0)
    status: ClaimStatusValue = "open"
    reviewer_note: str | None = Field(default=None, max_length=settings.claim_note_max_chars)

    @field_validator("claim_text")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Claim text is required.")
        return normalized

    @field_validator("reviewer_note")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    @model_validator(mode="after")
    def validate_offsets_pair(self) -> "ClaimBase":
        if (self.start_offset is None) != (self.end_offset is None):
            raise ValueError("Both start_offset and end_offset are required when using offsets.")
        if self.start_offset is not None and self.end_offset is not None and self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset.")
        return self


class ClaimCreate(ClaimBase):
    pass


class ClaimUpdate(BaseModel):
    claim_text: str | None = Field(default=None, min_length=settings.claim_text_min_chars, max_length=settings.claim_text_max_chars)
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, gt=0)
    status: ClaimStatusValue | None = None
    reviewer_note: str | None = Field(default=None, max_length=settings.claim_note_max_chars)

    @field_validator("claim_text")
    @classmethod
    def normalize_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Claim text is required.")
        return normalized

    @field_validator("reviewer_note")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    @model_validator(mode="after")
    def validate_offsets_pair(self) -> "ClaimUpdate":
        if (self.start_offset is None) != (self.end_offset is None):
            raise ValueError("Both start_offset and end_offset are required when using offsets.")
        if self.start_offset is not None and self.end_offset is not None and self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset.")
        return self


class EvidenceBase(BaseModel):
    source_url: str = Field(min_length=8, max_length=settings.evidence_url_max_chars)
    source_title: str | None = Field(default=None, max_length=settings.evidence_title_max_chars)
    publisher: str | None = Field(default=None, max_length=settings.evidence_publisher_max_chars)
    publication_date: datetime | None = None
    assessment: EvidenceAssessmentValue
    evidence_excerpt: str | None = Field(default=None, max_length=settings.evidence_excerpt_max_chars)
    reviewer_note: str | None = Field(default=None, max_length=settings.evidence_note_max_chars)

    @field_validator("source_url")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Source URL is required.")
        return normalized

    @field_validator("source_title", "publisher", "evidence_excerpt", "reviewer_note")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    source_url: str | None = Field(default=None, min_length=8, max_length=settings.evidence_url_max_chars)
    source_title: str | None = Field(default=None, max_length=settings.evidence_title_max_chars)
    publisher: str | None = Field(default=None, max_length=settings.evidence_publisher_max_chars)
    publication_date: datetime | None = None
    assessment: EvidenceAssessmentValue | None = None
    evidence_excerpt: str | None = Field(default=None, max_length=settings.evidence_excerpt_max_chars)
    reviewer_note: str | None = Field(default=None, max_length=settings.evidence_note_max_chars)

    @field_validator("source_url")
    @classmethod
    def normalize_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Source URL is required.")
        return normalized

    @field_validator("source_title", "publisher", "evidence_excerpt", "reviewer_note")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None


class EvidenceResponse(BaseModel):
    id: UUID
    claim_id: UUID
    source_url: str
    source_title: str | None
    publisher: str | None
    publication_date: datetime | None
    assessment: EvidenceAssessmentValue
    evidence_excerpt: str | None
    reviewer_note: str | None
    created_at: datetime
    updated_at: datetime


class ClaimEvidenceCounts(BaseModel):
    total: int
    supports: int
    contradicts: int
    neutral: int
    unclear: int


class ClaimResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    claim_text: str
    start_offset: int | None
    end_offset: int | None
    status: ClaimStatusValue
    reviewer_note: str | None
    evidence_counts: ClaimEvidenceCounts
    evidence: list[EvidenceResponse]
    created_at: datetime
    updated_at: datetime


class ClaimsListResponse(BaseModel):
    items: list[ClaimResponse]
    total: int
    limit: int
    offset: int


class DeleteClaimResponse(BaseModel):
    claim_id: UUID
    deleted: bool
    removed_evidence_count: int
    message: str


class DeleteEvidenceResponse(BaseModel):
    evidence_id: UUID
    deleted: bool
    message: str


class AnalysisEvidenceSummary(BaseModel):
    analysis_id: UUID
    total_claims: int
    claims_with_evidence: int
    claims_without_evidence: int
    total_evidence_references: int
    supporting_evidence_count: int
    contradicting_evidence_count: int
    neutral_evidence_count: int
    unclear_evidence_count: int
    evidence_coverage_percentage: float | None
    latest_evidence_updated_at: datetime | None
    interpretation: str


class EvidenceStatisticsResponse(BaseModel):
    analyses_with_claims: int
    total_claims: int
    total_evidence_records: int
    claims_with_evidence: int
    claims_without_evidence: int
    evidence_coverage_percentage: float | None
    assessment_distribution: dict[EvidenceAssessmentValue, int]
    latest_evidence_updated_at: datetime | None
    interpretation: str
