from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import ProcessMetrics, RequestContextMiddleware, SecurityHeadersMiddleware
from app.schemas.health import HealthResponse


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "REST API for the AI News Credibility & Misinformation Detection Platform. "
            "Predictions are model outputs; verified labels and evidence are human-entered."
        ),
        openapi_tags=[
            {"name": "health", "description": "Liveness, readiness, system metadata, and safe process metrics."},
            {"name": "dataset-imports", "description": "CSV import workflow and import-run history."},
            {"name": "articles", "description": "Paginated canonical article browsing."},
            {"name": "dataset-statistics", "description": "Aggregate statistics for imported labeled datasets."},
            {"name": "ml", "description": "Training runs, predictions, explanations, and model comparison."},
            {"name": "experiments", "description": "Experiment summaries, details, and comparison workflows."},
            {"name": "models", "description": "Champion, candidate, archived, promote, restore, and archive actions."},
            {"name": "history", "description": "Saved analyses and persisted prediction/explanation snapshots."},
            {"name": "evidence", "description": "Manual claims, reviewer-entered evidence references, and evidence summaries."},
            {"name": "monitoring", "description": "Reference profiles, drift diagnostics, confidence, and usage monitoring."},
            {"name": "reviews", "description": "Human-verified labels, review queue, performance, calibration, and errors."},
        ],
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.process_metrics = ProcessMetrics()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def root_health() -> HealthResponse:
        return HealthResponse(status="ok", service=settings.app_name)

    return app


app = create_app()
