from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.article import ArticleLabel
from app.models.training import ClassicalModelType, MLTrainingRun, ModelFamily, TrainingRunStatus
from app.ml.artifacts import ArtifactError
from app.ml.inference import InferenceService
from app.ml.transformer_artifacts import TRANSFORMER_ARTIFACT_VERSION, TransformerArtifactStore
from app.ml.transformer_dataset import ID2LABEL, LABEL2ID, tokenize_texts
from app.ml.transformer_inference import TransformerInferenceService
from app.ml.transformer_probabilities import prediction_from_logits, softmax_probabilities
from app.ml.transformer_training import TransformerDependencyError, TransformerTrainingService
from app.schemas.ml import PredictionRequest, TransformerConfig, TrainingRunCreate


class FakeTokenizer:
    def __call__(self, texts, truncation, padding, max_length, **_kwargs):
        assert truncation is True
        assert padding is True
        assert max_length == 32
        return {
            "input_ids": [[1, 2, 3] for _text in texts],
            "attention_mask": [[1, 1, 1] for _text in texts],
        }

    def save_pretrained(self, path: Path) -> None:
        (Path(path) / "tokenizer_config.json").write_text("{}", encoding="utf-8")


class FakeModel:
    def save_pretrained(self, path: Path) -> None:
        (Path(path) / "config.json").write_text("{}", encoding="utf-8")
        (Path(path) / "model.safetensors").write_text("weights", encoding="utf-8")


def test_transformer_training_config_validation() -> None:
    config = TrainingRunCreate(model_type=ClassicalModelType.DISTILBERT)

    assert config.model_family == ModelFamily.TRANSFORMER
    assert config.transformer.model_name == "distilbert-base-uncased"

    with pytest.raises(ValidationError):
        TransformerConfig(max_sequence_length=8)


def test_transformer_label_mappings_are_explicit() -> None:
    assert LABEL2ID == {"REAL": 0, "FAKE": 1}
    assert ID2LABEL == {0: "REAL", 1: "FAKE"}


def test_tokenizer_preparation_uses_hf_tokenizer_contract() -> None:
    encoded = tokenize_texts(FakeTokenizer(), ["One text", "Two text"], max_sequence_length=32)

    assert encoded["input_ids"] == [[1, 2, 3], [1, 2, 3]]
    assert encoded["attention_mask"] == [[1, 1, 1], [1, 1, 1]]


def test_softmax_probability_and_confidence_are_valid() -> None:
    probabilities = softmax_probabilities([1.0, 3.0])
    predicted_label, prediction_probabilities, confidence = prediction_from_logits([1.0, 3.0])

    assert predicted_label == ArticleLabel.FAKE
    assert 0 <= probabilities["REAL"] <= 1
    assert 0 <= probabilities["FAKE"] <= 1
    assert pytest.approx(probabilities["REAL"] + probabilities["FAKE"], abs=0.00001) == 1.0
    assert confidence == prediction_probabilities["FAKE"]


def test_transformer_artifact_metadata_and_path_safety(tmp_path: Path) -> None:
    store = TransformerArtifactStore(tmp_path)
    relative_path, checksum = store.save(
        training_run_id="00000000-0000-0000-0000-000000000001",
        model=FakeModel(),
        tokenizer=FakeTokenizer(),
        metadata={
            "model_family": "transformer",
            "model_type": "distilbert",
            "base_model_name": "distilbert-base-uncased",
            "label2id": LABEL2ID,
            "id2label": ID2LABEL,
            "transformer_config": TransformerConfig(max_sequence_length=32).model_dump(),
            "text_composition_config": {"mode": "title_and_content", "separator": "\n\n"},
        },
    )

    artifact_dir, metadata = store.load_metadata(relative_path)

    assert checksum == metadata["artifact_checksum"]
    assert metadata["artifact_version"] == TRANSFORMER_ARTIFACT_VERSION
    assert artifact_dir.name == "hf_model"
    with pytest.raises(ArtifactError):
        store.load_metadata("../outside")


def test_transformer_training_fails_clearly_without_dependencies(db_session: Session, tmp_path: Path, monkeypatch) -> None:
    import builtins

    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name in {"torch", "transformers"}:
            raise ImportError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    training_run = MLTrainingRun(
        model_family=ModelFamily.TRANSFORMER.value,
        model_type=ClassicalModelType.DISTILBERT.value,
        base_model_name="distilbert-base-uncased",
        model_display_name="Offline transformer",
        status=TrainingRunStatus.TRAINING.value,
        preprocessing_config={},
        text_composition_config={"mode": "title_and_content", "separator": "\n\n"},
        tfidf_config={},
        transformer_config=TransformerConfig(max_sequence_length=32).model_dump(),
        model_hyperparameters={},
        split_config={},
        random_seed=42,
        dataset_identifiers=[],
        split_distributions={},
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )

    with pytest.raises(TransformerDependencyError):
        TransformerTrainingService(db_session, tmp_path).train(
            training_run,
            TrainingRunCreate(
                model_type=ClassicalModelType.DISTILBERT,
                transformer=TransformerConfig(max_sequence_length=32),
            ),
        )


def test_inference_dispatches_to_transformer_service(db_session: Session, tmp_path: Path, monkeypatch) -> None:
    now = datetime.now(UTC)
    training_run = MLTrainingRun(
        model_family=ModelFamily.TRANSFORMER.value,
        model_type=ClassicalModelType.DISTILBERT.value,
        base_model_name="distilbert-base-uncased",
        model_display_name="Transformer run",
        status=TrainingRunStatus.COMPLETED.value,
        preprocessing_config={},
        text_composition_config={"mode": "title_and_content", "separator": "\n\n"},
        tfidf_config={},
        transformer_config=TransformerConfig(max_sequence_length=32).model_dump(),
        model_hyperparameters={},
        split_config={},
        random_seed=42,
        train_count=10,
        validation_count=2,
        test_count=2,
        dataset_article_count=14,
        dataset_identifiers=["fixture"],
        split_distributions={},
        artifact_path="transformer-run",
        artifact_checksum="checksum",
        artifact_version=TRANSFORMER_ARTIFACT_VERSION,
        probability_method="softmax_logits",
        started_at=now,
        completed_at=now,
        created_at=now,
    )
    db_session.add(training_run)
    db_session.commit()

    def fake_predict(self, run, request):
        assert run.id == training_run.id
        assert request.title == "Headline"
        return ArticleLabel.REAL, 0.8, 0.2, 0.8, "distilbert-base-uncased"

    monkeypatch.setattr(TransformerInferenceService, "predict", fake_predict)

    response = InferenceService(db_session, artifact_base_dir=tmp_path).predict(
        training_run.id,
        PredictionRequest(title="Headline", content="Article text"),
    )

    assert response.model_family == ModelFamily.TRANSFORMER
    assert response.model_type == ClassicalModelType.DISTILBERT
    assert response.model_name == "distilbert-base-uncased"
    assert response.real_probability == 0.8
    assert response.fake_probability == 0.2
    assert response.confidence == 0.8

