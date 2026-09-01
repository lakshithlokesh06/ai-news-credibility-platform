from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


def test_application_startup() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "AI News Credibility & Misinformation Detection Platform API"
    assert "AI News Credibility & Misinformation Detection Platform" in app.description


def test_root_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AI News Credibility & Misinformation Detection Platform API",
    }


def test_api_v1_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AI News Credibility & Misinformation Detection Platform API",
    }


def test_cors_preflight_allows_frontend_mutation_methods(client: TestClient) -> None:
    response = client.options(
        "/api/v1/history/00000000-0000-0000-0000-000000000000/review",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "PUT",
        },
    )
    assert response.status_code == 200
    assert "PUT" in response.headers["access-control-allow-methods"]
    assert "PATCH" in response.headers["access-control-allow-methods"]
