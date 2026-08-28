# AI News Credibility and Misinformation Detection Platform

Production-ready foundation for a full-stack AI/data-science platform that will eventually support model-based news credibility and misinformation analysis.

The current implementation includes the application foundation plus dataset ingestion, canonical article persistence, preprocessing utilities, dataset statistics, and data APIs. It does not implement fake-news prediction, model training, transformer inference, SHAP explainability, or generated prediction results.

## Purpose

This project is designed to grow into a platform that can analyze news headlines or articles using NLP, classical machine-learning baselines, transformer classifiers, confidence scoring, explainability, model comparison, and evaluation dashboards.

The future system should provide model-based credibility and misinformation predictions based on learned textual patterns. It should not claim to independently prove whether a story is objectively true or false.

## Current Status

- Monorepo scaffold with separate frontend and backend applications
- FastAPI backend with health endpoints, configuration, logging, CORS, exceptions, SQLAlchemy session setup, Alembic, article models, import tracking, ingestion services, preprocessing services, and dataset statistics
- Next.js frontend shell with professional product navigation, placeholder product pages, and a live data overview page
- PostgreSQL development database via Docker Compose
- Backend tests for startup, health endpoints, ingestion, preprocessing, statistics, and data APIs
- Documentation for the planned architecture and roadmap

## Technology Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- Database: PostgreSQL
- Testing: pytest, FastAPI TestClient
- Tooling: Docker Compose, ESLint, TypeScript

## Directory Structure

```text
.
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── explainability/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── nlp/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   └── tests/
├── data/
│   ├── processed/
│   └── raw/
├── docs/
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
└── models/
    ├── artifacts/
    ├── checkpoints/
    └── trained/
```

## Local Setup

Copy the root environment template and adjust values as needed:

```bash
cp .env.example .env
```

The backend and frontend also include their own `.env.example` files for app-specific local development.

## PostgreSQL

Start the local database:

```bash
docker compose up -d postgres
```

The default development database URL is:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/ai_news_credibility
```

## Backend

From the `backend/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Useful commands:

```bash
pytest
alembic upgrade head
```

The backend exposes:

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/dataset-imports`
- `GET /api/v1/dataset-imports/{import_run_id}`
- `POST /api/v1/dataset-imports`
- `GET /api/v1/articles`
- `GET /api/v1/articles/{article_id}`
- `GET /api/v1/dataset-statistics`

## Dataset Imports

Place CSV datasets in:

```text
data/raw/
```

Then trigger an import through the backend API:

```bash
curl -X POST http://localhost:8000/api/v1/dataset-imports \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "example-dataset",
    "filename": "example.csv",
    "column_mapping": {
      "title": "headline",
      "content": "text",
      "label": "label",
      "source_name": "source",
      "publication_date": "date",
      "source_url": "url"
    }
  }'
```

Only filenames inside `data/raw/` are accepted. Arbitrary filesystem paths are rejected.

Numeric labels require explicit meaning:

```json
{
  "dataset_name": "numeric-label-dataset",
  "filename": "numeric.csv",
  "label_mapping": {
    "1": "REAL",
    "0": "FAKE"
  }
}
```

The importer never infers labels from article content.

## Canonical Article Schema

Imported CSV rows are mapped into canonical `news_articles` records:

- `id`
- `title`
- `content`
- `label`: `REAL` or `FAKE`
- `source_name`
- `author`
- `publication_date`
- `source_url`
- `dataset_name`
- `external_id`
- `duplicate_key`
- `import_run_id`
- `created_at`
- `updated_at`

Optional fields may be absent in source datasets. A row must include an explicit label and at least a title/headline or content/article text.

## Preprocessing

The backend includes two reusable text paths:

- Classical ML preprocessing: Unicode normalization, HTML removal, whitespace normalization, configurable URL normalization/removal, configurable lowercasing, and conservative punctuation spacing.
- Transformer-safe preprocessing: minimal Unicode, HTML, and whitespace cleanup while preserving casing, punctuation, sentence structure, and contextual wording.

Article text composition is explicit and reproducible with `title_only`, `content_only`, and `title_and_content` modes.

## Frontend

From the `frontend/` directory:

```bash
npm install
cp .env.example .env.local
npm run dev
```

Useful commands:

```bash
npm run lint
npm run typecheck
npm run build
```

## Frontend Routes

- `/` - landing page
- `/data` - dataset overview, latest imports, and article browser
- `/analyze` - future article analysis workspace
- `/history` - future prediction history
- `/models` - future model comparison
- `/evaluation` - future evaluation dashboard
- `/about` - project information

## Roadmap

- Dataset import UI actions for server-local CSV files
- NLP preprocessing extensions for tokenization, optional stop-word handling, and feature extraction
- Classical ML baselines such as logistic regression, SVM, and tree-based models
- Transformer-based credibility and misinformation classification
- Confidence scoring and calibration
- SHAP-based explainability for model outputs where appropriate
- Model comparison dashboard
- Evaluation workflow with precision, recall, F1, ROC-AUC, calibration, and confusion matrices
- Prediction history and audit trail
- Dataset ingestion, provenance tracking, and experiment metadata
