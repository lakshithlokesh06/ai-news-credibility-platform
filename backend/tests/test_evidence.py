from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.evidence.service import EvidenceService
from app.models.analysis import AnalysisRecord, ExplanationStatus
from app.models.article import ArticleLabel
from app.models.evidence import AnalysisClaim, ClaimEvidence
from app.models.review import AnalysisReview
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, ModelLifecycleStatus, TrainingRunStatus


def make_run(db_session: Session, *, lifecycle_status: str | None = None) -> MLTrainingRun:
    now = datetime.now(UTC)
    run = MLTrainingRun(
        id=uuid4(),
        model_family=ModelFamily.CLASSICAL.value,
        model_type=ClassicalModelType.LOGISTIC_REGRESSION.value,
        base_model_name=None,
        model_display_name="Evidence model",
        status=TrainingRunStatus.COMPLETED.value,
        lifecycle_status=lifecycle_status,
        preprocessing_config={},
        text_composition_config={"mode": "title_and_content"},
        tfidf_config={},
        transformer_config={},
        model_hyperparameters={},
        split_config={},
        random_seed=11,
        train_count=10,
        validation_count=4,
        test_count=4,
        dataset_article_count=18,
        dataset_identifiers=["manual"],
        split_distributions={},
        validation_metrics={"accuracy": 0.75, "precision": 0.75, "recall": 0.75, "f1": 0.75, "roc_auc": 0.8},
        test_metrics={"accuracy": 0.75, "precision": 0.75, "recall": 0.75, "f1": 0.75, "roc_auc": 0.8},
        artifact_path="artifact",
        artifact_checksum="abc",
        artifact_version="1",
        probability_method="predict_proba",
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add(run)
    db_session.commit()
    return run


def make_analysis(db_session: Session, run: MLTrainingRun, *, predicted: ArticleLabel = ArticleLabel.FAKE) -> AnalysisRecord:
    now = datetime.now(UTC)
    analysis = AnalysisRecord(
        id=uuid4(),
        training_run_id=run.id,
        model_family=run.model_family,
        model_type=run.model_type,
        model_name=run.base_model_name,
        model_display_name=run.model_display_name,
        title="City council approves emergency bridge funding",
        content="City council approved emergency bridge funding after inspectors reported structural damage.",
        text_composition_mode="title_and_content",
        predicted_label=predicted.value,
        real_probability=0.25 if predicted == ArticleLabel.FAKE else 0.75,
        fake_probability=0.75 if predicted == ArticleLabel.FAKE else 0.25,
        confidence=0.75,
        probability_method="predict_proba",
        explanation_status=ExplanationStatus.GENERATED,
        explanation_method="coefficient_tfidf_local",
        explained_class=predicted.value,
        influences_toward_real=[],
        influences_toward_fake=[],
        explanation_limitations=[],
        explanation_generated_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


def add_review(db_session: Session, analysis: AnalysisRecord, *, label: ArticleLabel) -> None:
    now = datetime.now(UTC)
    db_session.add(
        AnalysisReview(
            id=uuid4(),
            analysis_id=analysis.id,
            verified_label=label.value,
            status="reviewed",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()


def add_claim(client: TestClient, analysis_id, claim_text: str = "City council approved bridge funding") -> dict:
    response = client.post(
        f"/api/v1/history/{analysis_id}/claims",
        json={"claim_text": claim_text, "reviewer_note": "manual claim"},
    )
    assert response.status_code == 201
    return response.json()


def add_evidence(client: TestClient, claim_id, *, assessment: str = "supports", source_url: str = "https://example.com/report") -> dict:
    response = client.post(
        f"/api/v1/claims/{claim_id}/evidence",
        json={
            "source_url": source_url,
            "source_title": "Inspection report",
            "publisher": "City Records",
            "assessment": assessment,
            "evidence_excerpt": "Manual excerpt from the report.",
            "reviewer_note": "Entered by reviewer.",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_claim_create_update_delete_and_offsets(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = make_analysis(db_session, run)
    claim_text = "City council approved emergency bridge funding"
    start = f"{analysis.title}\n\n{analysis.content}".index("City council approved")
    end = start + len(claim_text)

    created = client.post(
        f"/api/v1/history/{analysis.id}/claims",
        json={"claim_text": claim_text, "start_offset": start, "end_offset": end, "status": "open"},
    )
    assert created.status_code == 201
    claim_id = created.json()["id"]
    assert created.json()["claim_text"] == claim_text
    assert created.json()["evidence_counts"]["total"] == 0

    updated = client.patch(f"/api/v1/claims/{claim_id}", json={"status": "reviewed", "reviewer_note": "checked"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "reviewed"
    assert updated.json()["start_offset"] == start

    deleted = client.delete(f"/api/v1/claims/{claim_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert client.get(f"/api/v1/history/{analysis.id}").status_code == 200


def test_claim_validation_unknown_analysis_and_cascade(client: TestClient, db_session: Session) -> None:
    assert client.post(f"/api/v1/history/{uuid4()}/claims", json={"claim_text": "A sufficiently long claim"}).status_code == 404
    run = make_run(db_session)
    analysis = make_analysis(db_session, run)

    too_short = client.post(f"/api/v1/history/{analysis.id}/claims", json={"claim_text": "short"})
    assert too_short.status_code == 422
    blank_claim = client.post(f"/api/v1/history/{analysis.id}/claims", json={"claim_text": "          "})
    assert blank_claim.status_code == 422

    bad_offsets = client.post(
        f"/api/v1/history/{analysis.id}/claims",
        json={"claim_text": "City council approved emergency bridge funding", "start_offset": 0, "end_offset": 99999},
    )
    assert bad_offsets.status_code == 400
    assert bad_offsets.json()["detail"]["error_type"] == "invalid_claim_offsets"

    claim = add_claim(client, analysis.id)
    evidence = add_evidence(client, claim["id"])
    assert client.delete(f"/api/v1/history/{analysis.id}").status_code == 200
    assert db_session.execute(select(AnalysisClaim).where(AnalysisClaim.id == UUID(claim["id"]))).scalars().first() is None
    assert db_session.execute(select(ClaimEvidence).where(ClaimEvidence.id == UUID(evidence["id"]))).scalars().first() is None


def test_evidence_create_update_delete_validation_and_duplicates(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = make_analysis(db_session, run)
    claim = add_claim(client, analysis.id)
    evidence = add_evidence(client, claim["id"], source_url="HTTPS://Example.com/report/?b=2&a=1#section")

    duplicate = client.post(
        f"/api/v1/claims/{claim['id']}/evidence",
        json={"source_url": "https://example.com/report?a=1&b=2", "assessment": "neutral"},
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"]["error_type"] == "duplicate_evidence"

    invalid_scheme = client.post(
        f"/api/v1/claims/{claim['id']}/evidence",
        json={"source_url": "javascript:alert(1)", "assessment": "supports"},
    )
    assert invalid_scheme.status_code == 400
    blank_url = client.post(
        f"/api/v1/claims/{claim['id']}/evidence",
        json={"source_url": "          ", "assessment": "supports"},
    )
    assert blank_url.status_code == 422

    invalid_assessment = client.post(
        f"/api/v1/claims/{claim['id']}/evidence",
        json={"source_url": "https://example.com/other", "assessment": "proves_true"},
    )
    assert invalid_assessment.status_code == 422

    too_long = client.post(
        f"/api/v1/claims/{claim['id']}/evidence",
        json={"source_url": "https://example.com/" + ("x" * 3000), "assessment": "supports"},
    )
    assert too_long.status_code == 422

    updated = client.patch(
        f"/api/v1/evidence/{evidence['id']}",
        json={"assessment": "contradicts", "publisher": "Updated publisher"},
    )
    assert updated.status_code == 200
    assert updated.json()["assessment"] == "contradicts"
    assert updated.json()["publisher"] == "Updated publisher"

    cleared_metadata = client.patch(
        f"/api/v1/evidence/{evidence['id']}",
        json={"source_title": None, "publisher": None, "evidence_excerpt": None},
    )
    assert cleared_metadata.status_code == 200
    assert cleared_metadata.json()["source_title"] is None
    assert cleared_metadata.json()["publisher"] is None
    assert cleared_metadata.json()["evidence_excerpt"] is None

    deleted = client.delete(f"/api/v1/evidence/{evidence['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert client.get(f"/api/v1/history/{analysis.id}/claims").json()["items"][0]["evidence_counts"]["total"] == 0


def test_evidence_creation_does_not_perform_network(monkeypatch, client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = make_analysis(db_session, run)
    claim = add_claim(client, analysis.id)

    def fail_network(*_args, **_kwargs):
        raise AssertionError("Evidence creation must not open network connections")

    monkeypatch.setattr("socket.create_connection", fail_network)
    evidence = add_evidence(client, claim["id"], source_url="https://example.org/manual-reference")
    assert evidence["source_url"] == "https://example.org/manual-reference"


def test_summary_statistics_and_aggregate_privacy(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = make_analysis(db_session, run)
    claim_one = add_claim(client, analysis.id, "Inspectors reported structural bridge damage")
    claim_two = add_claim(client, analysis.id, "Emergency bridge funding was approved by council")
    add_evidence(client, claim_one["id"], assessment="supports", source_url="https://example.com/one")
    add_evidence(client, claim_one["id"], assessment="contradicts", source_url="https://example.com/two")
    add_evidence(client, claim_two["id"], assessment="neutral", source_url="https://example.com/three")

    summary = client.get(f"/api/v1/history/{analysis.id}/evidence-summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["total_claims"] == 2
    assert payload["claims_with_evidence"] == 2
    assert payload["supporting_evidence_count"] == 1
    assert payload["contradicting_evidence_count"] == 1
    assert payload["neutral_evidence_count"] == 1
    assert payload["evidence_coverage_percentage"] == 100
    assert payload["latest_evidence_updated_at"] is not None

    statistics = client.get("/api/v1/evidence/statistics")
    assert statistics.status_code == 200
    assert statistics.json()["total_claims"] == 2
    assert statistics.json()["total_evidence_records"] == 3
    assert statistics.json()["latest_evidence_updated_at"] is not None
    assert "example.com" not in statistics.text
    assert "Manual excerpt" not in statistics.text


def test_zero_claim_summary_has_unavailable_coverage(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = make_analysis(db_session, run)
    summary = client.get(f"/api/v1/history/{analysis.id}/evidence-summary").json()
    assert summary["total_claims"] == 0
    assert summary["evidence_coverage_percentage"] is None
    assert summary["latest_evidence_updated_at"] is None


def test_evidence_does_not_change_review_or_performance(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session)
    analysis = make_analysis(db_session, run, predicted=ArticleLabel.FAKE)
    add_review(db_session, analysis, label=ArticleLabel.FAKE)
    before = client.get("/api/v1/reviews/performance", params={"training_run_id": str(run.id)}).json()

    claim = add_claim(client, analysis.id)
    evidence = add_evidence(client, claim["id"], assessment="contradicts")
    after_create = client.get("/api/v1/reviews/performance", params={"training_run_id": str(run.id)}).json()
    detail = client.get(f"/api/v1/history/{analysis.id}").json()
    assert detail["review"]["verified_label"] == "FAKE"
    assert before["accuracy"] == after_create["accuracy"]
    assert before["precision"] == after_create["precision"]
    assert before["recall"] == after_create["recall"]
    assert before["f1"] == after_create["f1"]
    assert before["roc_auc"] == after_create["roc_auc"]

    assert client.patch(f"/api/v1/evidence/{evidence['id']}", json={"assessment": "supports"}).status_code == 200
    assert client.delete(f"/api/v1/evidence/{evidence['id']}").status_code == 200
    after_delete = client.get("/api/v1/reviews/performance", params={"training_run_id": str(run.id)}).json()
    assert after_delete["accuracy"] == before["accuracy"]
    assert client.get(f"/api/v1/history/{analysis.id}").json()["predicted_label"] == "FAKE"


def test_evidence_does_not_change_lifecycle(client: TestClient, db_session: Session) -> None:
    run = make_run(db_session, lifecycle_status=ModelLifecycleStatus.CHAMPION.value)
    analysis = make_analysis(db_session, run)
    claim = add_claim(client, analysis.id)
    add_evidence(client, claim["id"], assessment="contradicts")

    db_session.refresh(run)
    assert run.lifecycle_status == ModelLifecycleStatus.CHAMPION.value


def test_url_normalization_is_local_and_deterministic() -> None:
    assert (
        EvidenceService.normalize_url("HTTPS://Example.COM/path/?b=2&a=1#frag")
        == "https://example.com/path?a=1&b=2"
    )
