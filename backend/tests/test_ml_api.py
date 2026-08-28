from pathlib import Path

from fastapi.testclient import TestClient


def seed_dataset(client: TestClient, tmp_path: Path, samples_per_class: int = 12) -> None:
    rows = ["title,content,label"]
    for index in range(samples_per_class):
        rows.append(
            f"Verified report {index},confirmed evidence official record committee {index},REAL"
        )
        rows.append(
            f"Viral hoax {index},fabricated rumor conspiracy invented shocking claim {index},FAKE"
        )
    (tmp_path / "ml_api_fixture.csv").write_text("\n".join(rows), encoding="utf-8")
    response = client.post(
        "/api/v1/dataset-imports",
        json={"dataset_name": "ml-api-fixture", "filename": "ml_api_fixture.csv"},
    )
    assert response.status_code == 201


def test_training_api_handles_empty_dataset(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ml/training-runs",
        json={"model_type": "logistic_regression"},
    )

    assert response.status_code == 400
    assert "Training could not safely proceed" in response.json()["detail"]["message"]


def test_training_inference_and_comparison_api(client: TestClient, tmp_path: Path) -> None:
    seed_dataset(client, tmp_path)

    train_response = client.post(
        "/api/v1/ml/training-runs",
        json={
            "model_type": "linear_svm",
            "text_composition": {"mode": "title_and_content"},
            "tfidf": {"max_features": 500, "ngram_min": 1, "ngram_max": 2},
            "hyperparameters": {"calibration_cv": 2, "max_iter": 2000},
            "random_seed": 11,
        },
    )
    assert train_response.status_code == 201
    training_run = train_response.json()
    assert training_run["status"] == "completed"
    assert training_run["artifact_path"] is not None

    list_response = client.get("/api/v1/ml/training-runs")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = client.get(f"/api/v1/ml/training-runs/{training_run['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["test_metrics"]["f1"] is not None

    predict_response = client.post(
        f"/api/v1/ml/models/{training_run['id']}/predict",
        json={
            "title": "Verified report",
            "content": "confirmed evidence official record committee",
        },
    )
    assert predict_response.status_code == 200
    prediction = predict_response.json()
    assert prediction["predicted_label"] in {"REAL", "FAKE"}
    assert prediction["real_probability"] is not None
    assert prediction["fake_probability"] is not None
    assert prediction["confidence"] is not None

    comparison_response = client.get("/api/v1/ml/model-comparison")
    assert comparison_response.status_code == 200
    comparison = comparison_response.json()
    assert comparison["metric_source"] == "test"
    assert len(comparison["items"]) == 1
    assert comparison["recommended_training_run_id"] == training_run["id"]

