from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.ml.transformer_artifacts import TRANSFORMER_ARTIFACT_VERSION
from app.ml.transformer_training import TransformerTrainingService
from app.models.training import TrainingRunStatus


def test_transformer_training_api_records_mocked_completed_run(client: TestClient, monkeypatch) -> None:
    def fake_train(self, training_run, config):
        training_run.train_count = 8
        training_run.validation_count = 2
        training_run.test_count = 2
        training_run.dataset_article_count = 12
        training_run.dataset_identifiers = ["mocked-transformer"]
        training_run.split_distributions = {
            "train": {"REAL": 4, "FAKE": 4},
            "validation": {"REAL": 1, "FAKE": 1},
            "test": {"REAL": 1, "FAKE": 1},
        }
        training_run.validation_metrics = {"f1": 0.5, "accuracy": 0.5, "roc_auc": 0.5}
        training_run.test_metrics = {"f1": 0.75, "accuracy": 0.75, "roc_auc": 0.75}
        training_run.artifact_path = str(training_run.id)
        training_run.artifact_checksum = "checksum"
        training_run.artifact_version = TRANSFORMER_ARTIFACT_VERSION
        training_run.probability_method = "softmax_logits"
        training_run.device_used = "cpu"
        training_run.training_duration_seconds = 0.1
        training_run.completed_at = datetime.now(UTC)

    monkeypatch.setattr(TransformerTrainingService, "train", fake_train)

    response = client.post(
        "/api/v1/ml/training-runs",
        json={
            "model_type": "distilbert",
            "transformer": {
                "model_name": "distilbert-base-uncased",
                "max_sequence_length": 64,
                "batch_size": 2,
                "epochs": 1,
                "device_preference": "cpu",
            },
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["model_family"] == "transformer"
    assert payload["model_type"] == "distilbert"
    assert payload["base_model_name"] == "distilbert-base-uncased"
    assert payload["status"] == TrainingRunStatus.COMPLETED.value
    assert payload["device_used"] == "cpu"

    comparison = client.get("/api/v1/ml/model-comparison").json()
    assert comparison["items"][0]["model_family"] == "transformer"
    assert comparison["items"][0]["base_model_name"] == "distilbert-base-uncased"

