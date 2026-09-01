# AI News Credibility & Misinformation Detection Platform

A full-stack machine learning platform for analyzing news text, comparing credibility classifiers, explaining model predictions, monitoring model behavior, and supporting structured human review.

This project demonstrates applied NLP, ML model operations, explainability, production-oriented API design, and responsible review workflows. It is an ML-based analysis and evaluation platform, not an automated truth engine.

## Overview

News Credibility AI lets a local evaluator import labeled news datasets, train credibility classifiers, inspect validation/test metrics, promote an explicit champion model, analyze new articles, explain model predictions, save analysis history, assign human-verified labels, record manual claims/evidence, and inspect reviewed-production performance and monitoring diagnostics.

Predictions are model outputs. Confidence is model confidence. SHAP and feature attribution explain model behavior. Manual evidence is reviewer-entered. Verified labels are human-entered. The system does not independently prove factual truth.

## Key Features

- CSV dataset ingestion with canonical article storage, explicit label mapping, duplicate handling, and dataset statistics
- Classical NLP pipeline with preprocessing, TF-IDF, Logistic Regression, and calibrated Linear SVM
- DistilBERT transformer training/inference support with lazy dependency loading
- Reproducible train/validation/test splits, stored hyperparameters, dataset identifiers, preprocessing config, and artifact metadata
- Model registry, experiment comparison, candidate/champion/archive lifecycle, and explicit champion selection
- Model prediction API with REAL/FAKE probabilities, confidence, and optional persisted analysis history
- SHAP and feature-attribution explainability for model behavior inspection
- Monitoring reference profiles, input drift, prediction drift, confidence diagnostics, and usage windows
- Human review with manual verified labels, reviewed-production performance, calibration diagnostics, and error analysis
- Manual claim and evidence workspace with reviewer-entered URLs and supports/contradicts/neutral/unclear assessments
- Production-oriented safeguards: request IDs, structured logging, rate limits, concurrency controls, input bounds, readiness checks, security headers, CORS validation, Docker Compose, and tests

## System Architecture

```text
Next.js Frontend
-> FastAPI REST API
-> ML / Review / Evidence / Monitoring Services
-> PostgreSQL + Model Artifact Storage
```

PostgreSQL stores structured application data: articles, imports, training-run metadata, history, reviews, claims, evidence records, lifecycle events, and monitoring profiles. Model binaries and vectorizers are stored as controlled filesystem artifacts under `models/trained/`, not in PostgreSQL.

Detailed architecture notes: [docs/architecture.md](docs/architecture.md).

## Machine Learning Models

- **Logistic Regression**: interpretable classical TF-IDF baseline with probability output.
- **Calibrated Linear SVM**: sparse-text baseline with sigmoid calibration for probability estimates.
- **DistilBERT**: transformer classifier path for contextual text representation.

No model is claimed to be universally best. Experiment pages compare persisted validation/test metrics and warn when runs are not directly comparable.

## Responsible AI Design

- **Prediction**: likely credible or likely misinformation based on learned patterns.
- **Confidence**: model confidence, not truth probability or factual certainty.
- **Explainability**: SHAP/influence analysis shows which features affected the model prediction. Explanation is not factual evidence.
- **Human review**: verified REAL/FAKE labels are manually entered by reviewers.
- **Evidence**: claims and evidence URLs are manually entered. URLs are validated syntactically and stored, but not fetched, crawled, scraped, previewed, scored, or fact-checked automatically.
- **Monitoring**: drift and confidence diagnostics show behavior changes, not direct accuracy degradation.

Manual evidence workflow: [docs/evidence-review.md](docs/evidence-review.md).

## Tech Stack

**Frontend**: Next.js, React, TypeScript, Tailwind CSS, lucide-react

**Backend**: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL

**ML/NLP**: scikit-learn, NumPy, SHAP, PyTorch, Hugging Face Transformers, joblib

**Infrastructure**: Docker, Docker Compose, pytest, ESLint, TypeScript

## Project Structure

```text
.
├── backend/          # FastAPI app, ML services, migrations, tests
├── frontend/         # Next.js app, UI components, API client types
├── data/             # raw/processed data directories plus synthetic demo CSV
├── docs/             # architecture, security, deployment, demo, release docs
├── models/           # artifact/checkpoint/trained model directories
├── docker-compose.yml
├── .env.example
└── CHANGELOG.md
```

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/api/v1/readiness`

For manual local development:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## Demo Workflow

The repository includes `data/raw/demo_synthetic_news.csv`, a small synthetic CSV for demonstrating ingestion and training.

This synthetic dataset is for demonstrating application functionality only and must not be used to evaluate real-world misinformation detection accuracy.

Recommended demo path:

1. Start PostgreSQL/backend/frontend.
2. Import `demo_synthetic_news.csv` through `POST /api/v1/dataset-imports`.
3. Visit `/data` to inspect imported records and label distribution.
4. Train Logistic Regression or Linear SVM from `/models`.
5. Promote a completed run from `/experiments`.
6. Analyze an article from `/analyze`.
7. Request an explanation.
8. Open saved history, assign a human-verified label, and add claims/evidence.
9. Inspect `/performance` and `/monitoring`.

Practical walkthrough: [docs/demo-guide.md](docs/demo-guide.md).

## API Overview

Major API groups:

- `health/system`: liveness, readiness, system info, process metrics
- `dataset`: dataset imports, article browsing, dataset statistics
- `ML/training`: training runs, prediction, explanation, model comparison
- `models`: champion lookup, promotion, archive, restore
- `experiments`: experiment summaries, details, comparison
- `history`: saved analyses and persisted explanations
- `reviews`: human labels, queue, reviewed performance, calibration, errors
- `evidence`: manual claims, evidence references, evidence summaries/statistics
- `monitoring`: reference profiles, drift, confidence, usage diagnostics

OpenAPI is available at `/docs` in development when `DOCS_ENABLED=true`.

## Testing

Backend:

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/alembic history
.venv/bin/alembic upgrade head --sql
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Docker:

```bash
docker compose config
docker compose build
```

## Screenshots

No fabricated screenshots are committed. Recommended screenshot paths after capturing the running app:

- `docs/screenshots/analyze.png`
- `docs/screenshots/models.png`
- `docs/screenshots/monitoring.png`
- `docs/screenshots/review.png`
- `docs/screenshots/performance.png`
- `docs/screenshots/evidence.png`

## Documentation

- [Architecture](docs/architecture.md)
- [Security Notes](docs/security.md)
- [Deployment Guide](docs/deployment.md)
- [Manual Evidence Review](docs/evidence-review.md)
- [Demo Guide](docs/demo-guide.md)
- [Portfolio Notes](docs/portfolio-notes.md)
- [Release Checklist](docs/release-checklist.md)
- [Changelog](CHANGELOG.md)

## Limitations

- Model prediction is not factual verification.
- Dataset quality and representativeness strongly affect results.
- Human reviews, claims, and evidence assessments are manually entered and depend on reviewer judgment.
- Evidence URLs are not automatically fetched, validated for factual correctness, or fact-checked.
- Monitoring drift does not equal accuracy degradation.
- Reviewed metrics require enough human-verified labels.
- Rate limiting and concurrency controls are process-local.
- The current app has no authentication, RBAC, distributed task queue, distributed rate limiting, or production observability service.
- There is no automatic retraining, automatic model deployment, live news ingestion, source reputation scoring, or automated external fact checking.

The current release is most appropriate for development, education, portfolio demonstration, and controlled evaluation.

## Future Improvements

- Authentication and role-based access control
- Distributed training/task queue
- Distributed rate limiting and production observability
- CI/CD and automated deployment checks
- Cloud object storage for model artifacts
- Larger benchmark datasets and more transformer options
- Strictly sandboxed external evidence retrieval with SSRF protections
- Export workflows for reviews, evidence, and monitoring reports

## Portfolio Notes

This project is suitable as a portfolio demonstration of full-stack ML engineering: data ingestion, reproducible NLP training, explainable inference, model registry/lifecycle workflows, monitoring, and responsible human review. See [docs/portfolio-notes.md](docs/portfolio-notes.md) for resume bullets and interview talking points.
