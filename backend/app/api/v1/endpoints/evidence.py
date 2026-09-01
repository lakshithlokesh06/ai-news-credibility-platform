from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.evidence.service import EvidenceError, EvidenceService
from app.models.training import ModelFamily
from app.schemas.evidence import (
    AnalysisEvidenceSummary,
    ClaimCreate,
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

router = APIRouter()


def _evidence_error(exc: EvidenceError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if exc.error_type in {"analysis_not_found", "claim_not_found", "evidence_not_found"}
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(status_code=status_code, detail={"message": str(exc), "error_type": exc.error_type})


@router.post("/history/{analysis_id}/claims", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    analysis_id: UUID,
    request: ClaimCreate,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> ClaimResponse:
    try:
        return EvidenceService(db).create_claim(analysis_id, request)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc


@router.get("/history/{analysis_id}/claims", response_model=ClaimsListResponse)
async def list_claims(
    analysis_id: UUID,
    search: str | None = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> ClaimsListResponse:
    try:
        return EvidenceService(db).list_claims(analysis_id, search=search, limit=limit, offset=offset)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc


@router.get("/history/{analysis_id}/evidence-summary", response_model=AnalysisEvidenceSummary)
async def analysis_evidence_summary(
    analysis_id: UUID,
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> AnalysisEvidenceSummary:
    try:
        return EvidenceService(db).analysis_summary(analysis_id)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc


@router.patch("/claims/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: UUID,
    request: ClaimUpdate,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> ClaimResponse:
    try:
        return EvidenceService(db).update_claim(claim_id, request)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc


@router.delete("/claims/{claim_id}", response_model=DeleteClaimResponse)
async def delete_claim(
    claim_id: UUID,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> DeleteClaimResponse:
    try:
        return EvidenceService(db).delete_claim(claim_id)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc


@router.post("/claims/{claim_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    claim_id: UUID,
    request: EvidenceCreate,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    try:
        return EvidenceService(db).create_evidence(claim_id, request)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc


@router.get("/evidence/statistics", response_model=EvidenceStatisticsResponse)
async def evidence_statistics(
    training_run_id: UUID | None = Query(default=None),
    model_family: ModelFamily | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    _rate_limit: None = rate_limit("monitoring"),
    db: Session = Depends(get_db),
) -> EvidenceStatisticsResponse:
    return EvidenceService(db).statistics(
        training_run_id=training_run_id,
        model_family=model_family,
        search=search,
    )


@router.patch("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: UUID,
    request: EvidenceUpdate,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    try:
        return EvidenceService(db).update_evidence(evidence_id, request)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc


@router.delete("/evidence/{evidence_id}", response_model=DeleteEvidenceResponse)
async def delete_evidence(
    evidence_id: UUID,
    _rate_limit: None = rate_limit("mutation"),
    db: Session = Depends(get_db),
) -> DeleteEvidenceResponse:
    try:
        return EvidenceService(db).delete_evidence(evidence_id)
    except EvidenceError as exc:
        raise _evidence_error(exc) from exc

