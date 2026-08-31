# Deployment Guide

This guide describes a provider-neutral deployment shape for the current stack: Next.js, FastAPI, PostgreSQL, and local filesystem storage for datasets and model artifacts.

## Prerequisites

- PostgreSQL 16 or compatible
- Python 3.12+ for the backend
- Node.js 22+ for the frontend
- Persistent storage for `data/raw` and `models/trained`

## Backend Configuration

Important variables:

- `APP_ENV`: `development`, `test`, or `production`
- `DEBUG`: keep `false` in production
- `DOCS_ENABLED`: use `false` in production unless intentionally exposing OpenAPI docs
- `DATABASE_URL`: PostgreSQL SQLAlchemy URL
- `BACKEND_CORS_ORIGINS`: comma-separated frontend origins; no wildcard in production
- `LOG_LEVEL`: `INFO`, `WARNING`, `ERROR`, etc.
- `MAX_ARTICLE_TITLE_CHARS`, `MAX_ARTICLE_CONTENT_CHARS`, `MAX_COMBINED_ARTICLE_CHARS`
- `MAX_DATASET_FILE_BYTES`
- `TRAINING_CONCURRENCY_LIMIT`, `EXPLANATION_CONCURRENCY_LIMIT`
- `RATE_LIMIT_WINDOW_SECONDS` plus per-operation rate limit variables

## Frontend Configuration

Set `NEXT_PUBLIC_API_BASE_URL` to the externally reachable backend origin. The frontend and backend do not need to share a host.

## Migration Workflow

1. Configure environment variables.
2. Provision PostgreSQL.
3. Run Alembic migrations from `backend/`:

```bash
alembic upgrade head
```

4. Start the backend.
5. Start the frontend.
6. Verify `/health`, `/api/v1/health`, `/api/v1/readiness`, and `/api/v1/system/info`.

Do not run destructive migrations automatically from arbitrary web workers.

## Backend Runtime

For local source deployment:

```bash
cd backend
python -m pip install .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Do not use `--reload` in production.

## Frontend Runtime

```bash
cd frontend
npm ci
npm run build
npm run start
```

## Docker Compose

The root `docker-compose.yml` includes PostgreSQL, a one-shot migration service, backend, and frontend services with health checks and persistent model storage. For local development:

```bash
docker compose up --build
```

The `migrate` service runs `alembic upgrade head` after PostgreSQL is healthy and before the backend readiness check is expected to pass. To run migrations manually after changing schema code:

```bash
docker compose run --rm migrate
```

## Health And Readiness

- `/health` and `/api/v1/health`: process liveness
- `/api/v1/readiness`: database, schema, storage, and champion artifact metadata checks
- `/api/v1/system/info`: safe application metadata
- `/api/v1/system/metrics`: safe in-process request counters

Readiness does not load ML models.

## Persistence

Persist PostgreSQL data and `models/trained`. Keep imported raw datasets and model artifacts out of Git. Backups are an operational responsibility outside this application.

## Caveats

The current app has no authentication, no TLS termination, no distributed rate limiting, and no external observability service. Terminate HTTPS at a reverse proxy or deployment platform and add authentication before exposing sensitive workflows to untrusted users.
