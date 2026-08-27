from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


def test_application_startup() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "AI News Credibility API"


def test_root_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AI News Credibility API",
    }


def test_api_v1_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AI News Credibility API",
    }

