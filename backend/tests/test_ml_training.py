from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models.article import NewsArticle
from app.models.training import ClassicalModelType, TrainingRunStatus
from app.ml.artifacts import ArtifactError, ArtifactStore, resolve_artifact_dir
from app.ml.dataset import TrainingDatasetBuilder, TrainingDatasetError
from app.ml.features import create_tfidf_vectorizer
from app.ml.inference import InferenceService
from app.ml.splitting import stratified_split
from app.ml.training_service import TrainingService
from app.schemas.ml import (
    ModelHyperparameters,
    PredictionRequest,
    SplitConfig,
    TfidfConfig,
    TrainingRunCreate,
)
from app.schemas.preprocessing import TextCompositionConfig


def add_article(
    db_session: Session,
    *,
    index: int,
    label: str,
    dataset_name: str = "ml-fixture",
) -> NewsArticle:
    now = datetime.now(UTC)
    if label == "REAL":
        title = f"Verified public report {index}"
        content = f"confirmed evidence official statement budget committee verified record {index}"
    else:
        title = f"Sensational rumor claim {index}"
        content = f"fabricated hoax viral conspiracy invented shocking rumor claim {index}"
    article = NewsArticle(
        title=title,
        content=content,
        label=label,
        source_name="Synthetic test source",
        dataset_name=dataset_name,
        duplicate_key=f"{dataset_name}-{label}-{index}",
        created_at=now,
        updated_at=now,
    )
    db_session.add(article)
    return article


def add_balanced_articles(db_session: Session, samples_per_class: int = 12) -> None:
    for index in range(samples_per_class):
        add_article(db_session, index=index, label="REAL")
        add_article(db_session, index=index, label="FAKE")
    db_session.commit()


def small_training_config(model_type: ClassicalModelType) -> TrainingRunCreate:
    return TrainingRunCreate(
        model_type=model_type,
        text_composition=TextCompositionConfig(mode="title_and_content"),
        tfidf=TfidfConfig(max_features=500, ngram_min=1, ngram_max=2),
        hyperparameters=ModelHyperparameters(calibration_cv=2, max_iter=2000),
        random_seed=123,
    )


def test_training_dataset_preparation_validates_balanced_data(db_session: Session) -> None:
    add_balanced_articles(db_session)

    samples = TrainingDatasetBuilder(db_session).build(
        dataset_names=None,
        composition_config=TextCompositionConfig(),
        preprocessing_config=small_training_config(ClassicalModelType.LOGISTIC_REGRESSION).preprocessing,
    )

    assert len(samples) == 24
    assert {sample.label for sample in samples} == {"REAL", "FAKE"}
    assert all(sample.text for sample in samples)


def test_training_dataset_rejects_single_class(db_session: Session) -> None:
    for index in range(8):
        add_article(db_session, index=index, label="REAL")
    db_session.commit()

    with pytest.raises(TrainingDatasetError, match="both REAL and FAKE"):
        TrainingDatasetBuilder(db_session).build(
            dataset_names=None,
            composition_config=TextCompositionConfig(),
            preprocessing_config=small_training_config(ClassicalModelType.LOGISTIC_REGRESSION).preprocessing,
        )


def test_training_dataset_rejects_insufficient_samples(db_session: Session) -> None:
    add_balanced_articles(db_session, samples_per_class=3)

    with pytest.raises(TrainingDatasetError, match="At least 6 samples per class"):
        TrainingDatasetBuilder(db_session).build(
            dataset_names=None,
            composition_config=TextCompositionConfig(),
            preprocessing_config=small_training_config(ClassicalModelType.LOGISTIC_REGRESSION).preprocessing,
        )


def test_stratified_split_is_deterministic_and_non_overlapping(db_session: Session) -> None:
    add_balanced_articles(db_session)
    samples = TrainingDatasetBuilder(db_session).build(
        dataset_names=None,
        composition_config=TextCompositionConfig(),
        preprocessing_config=small_training_config(ClassicalModelType.LOGISTIC_REGRESSION).preprocessing,
    )

    first = stratified_split(samples, SplitConfig(), random_seed=42)
    second = stratified_split(samples, SplitConfig(), random_seed=42)

    assert first.train_ids == second.train_ids
    assert set(first.train_ids).isdisjoint(first.validation_ids)
    assert set(first.train_ids).isdisjoint(first.test_ids)
    assert first.distributions["train"]["REAL"] == first.distributions["train"]["FAKE"]
    assert first.distributions["validation"]["REAL"] == first.distributions["validation"]["FAKE"]
    assert first.distributions["test"]["REAL"] == first.distributions["test"]["FAKE"]


def test_tfidf_is_fit_only_on_training_text() -> None:
    vectorizer = create_tfidf_vectorizer(TfidfConfig(max_features=500, ngram_min=1, ngram_max=1))
    train_features = vectorizer.fit_transform(["known token", "another known"])
    validation_features = vectorizer.transform(["unseen validationtoken"])

    assert train_features.shape[0] == 2
    assert "validationtoken" not in vectorizer.vocabulary_
    assert validation_features.shape[1] == train_features.shape[1]


@pytest.mark.parametrize(
    "model_type",
    [ClassicalModelType.LOGISTIC_REGRESSION, ClassicalModelType.LINEAR_SVM],
)
def test_classical_model_training_persists_artifacts(
    db_session: Session,
    tmp_path: Path,
    model_type: ClassicalModelType,
) -> None:
    add_balanced_articles(db_session)

    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        small_training_config(model_type)
    )

    assert training_run.status == TrainingRunStatus.COMPLETED.value
    assert training_run.train_count > training_run.validation_count
    assert training_run.validation_metrics is not None
    assert training_run.test_metrics is not None
    assert training_run.test_metrics["f1"] is not None
    assert training_run.artifact_path is not None
    assert (tmp_path / training_run.artifact_path / "model.joblib").exists()
    assert training_run.probability_method is not None


def test_failed_training_run_is_recorded(db_session: Session, tmp_path: Path) -> None:
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        small_training_config(ClassicalModelType.LOGISTIC_REGRESSION)
    )

    assert training_run.status == TrainingRunStatus.FAILED.value
    assert "labeled dataset" in str(training_run.error_summary)


def test_artifact_loading_and_path_safety(db_session: Session, tmp_path: Path) -> None:
    add_balanced_articles(db_session)
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        small_training_config(ClassicalModelType.LOGISTIC_REGRESSION)
    )

    payload, metadata = ArtifactStore(tmp_path).load(training_run.artifact_path or "")

    assert metadata["artifact_version"] == "classical-ml-v1"
    assert "classifier" in payload
    with pytest.raises(ArtifactError):
        resolve_artifact_dir("../outside", tmp_path)


def test_inference_returns_valid_probabilities_and_confidence(db_session: Session, tmp_path: Path) -> None:
    add_balanced_articles(db_session)
    training_run = TrainingService(db_session, artifact_base_dir=tmp_path).train(
        small_training_config(ClassicalModelType.LOGISTIC_REGRESSION)
    )

    response = InferenceService(db_session, artifact_base_dir=tmp_path).predict(
        training_run.id,
        PredictionRequest(
            title="Verified public report",
            content="confirmed evidence official statement verified record",
        ),
    )

    assert response.predicted_label in {"REAL", "FAKE"}
    assert response.real_probability is not None
    assert response.fake_probability is not None
    assert pytest.approx(response.real_probability + response.fake_probability, abs=0.00001) == 1.0
    assert response.confidence in {response.real_probability, response.fake_probability}
    assert "not independent verification" in response.message

