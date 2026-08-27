# AI News Credibility and Misinformation Detection Platform

Production-ready foundation for a full-stack AI/data-science platform that will eventually support model-based news credibility and misinformation analysis.

The current implementation intentionally stops at the project foundation. It does not implement fake-news prediction, NLP preprocessing, model training, transformer inference, SHAP explainability, or generated prediction results.

## Purpose

This project is designed to grow into a platform that can analyze news headlines or articles using NLP, classical machine-learning baselines, transformer classifiers, confidence scoring, explainability, model comparison, and evaluation dashboards.

The future system should provide model-based credibility and misinformation predictions based on learned textual patterns. It should not claim to independently prove whether a story is objectively true or false.

## Current Status

- Monorepo scaffold with separate frontend and backend applications
- FastAPI backend with health endpoints, configuration, logging, CORS, exceptions, SQLAlchemy session setup, and Alembic
- Next.js frontend shell with professional product navigation and placeholder pages
- PostgreSQL development database via Docker Compose
- Backend tests for startup and health endpoints
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
- `/analyze` - future article analysis workspace
- `/history` - future prediction history
- `/models` - future model comparison
- `/evaluation` - future evaluation dashboard
- `/about` - project information

## Roadmap

- NLP preprocessing pipeline for cleaning, tokenization, normalization, and feature extraction
- Classical ML baselines such as logistic regression, SVM, and tree-based models
- Transformer-based credibility and misinformation classification
- Confidence scoring and calibration
- SHAP-based explainability for model outputs where appropriate
- Model comparison dashboard
- Evaluation workflow with precision, recall, F1, ROC-AUC, calibration, and confusion matrices
- Prediction history and audit trail
- Dataset ingestion, provenance tracking, and experiment metadata

