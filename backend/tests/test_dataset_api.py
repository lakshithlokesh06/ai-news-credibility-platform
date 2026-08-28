from pathlib import Path

from fastapi.testclient import TestClient


def test_statistics_api_returns_empty_state_without_fabrication(client: TestClient) -> None:
    response = client.get("/api/v1/dataset-statistics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_articles"] == 0
    assert payload["real_count"] == 0
    assert payload["fake_count"] == 0
    assert payload["average_article_length"] is None
    assert payload["dataset_distribution"] == []


def test_dataset_import_and_article_api(client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "api_fixture.csv").write_text(
        "\n".join(
            [
                "title,content,label,source,date",
                "Verified item,Plain source report,REAL,Wire,2026-01-01",
                "Fabricated item,Sensational made-up claim,FAKE,Blog,2026-01-02",
            ]
        ),
        encoding="utf-8",
    )

    import_response = client.post(
        "/api/v1/dataset-imports",
        json={"dataset_name": "api-fixture", "filename": "api_fixture.csv"},
    )
    assert import_response.status_code == 201
    import_payload = import_response.json()
    assert import_payload["status"] == "COMPLETED"
    assert import_payload["successfully_imported_rows"] == 2

    list_imports_response = client.get("/api/v1/dataset-imports")
    assert list_imports_response.status_code == 200
    assert list_imports_response.json()["total"] == 1

    articles_response = client.get("/api/v1/articles", params={"label": "REAL"})
    assert articles_response.status_code == 200
    articles_payload = articles_response.json()
    assert articles_payload["total"] == 1
    assert articles_payload["items"][0]["title"] == "Verified item"

    article_id = articles_payload["items"][0]["id"]
    article_response = client.get(f"/api/v1/articles/{article_id}")
    assert article_response.status_code == 200
    assert article_response.json()["dataset_name"] == "api-fixture"

    stats_response = client.get("/api/v1/dataset-statistics")
    assert stats_response.status_code == 200
    assert stats_response.json()["total_articles"] == 2


def test_import_api_rejects_unsafe_filename(client: TestClient) -> None:
    response = client.post(
        "/api/v1/dataset-imports",
        json={"dataset_name": "unsafe", "filename": "../outside.csv"},
    )

    assert response.status_code == 422

