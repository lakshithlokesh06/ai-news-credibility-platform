# Architecture

## Current Foundation

The project is structured as a modular full-stack monorepo:

```text
Frontend -> FastAPI -> NLP/ML Services -> PostgreSQL
```

The current foundation includes the frontend application shell, backend API skeleton, database connectivity setup, Alembic migrations, and documentation. Prediction, training, model loading, NLP preprocessing, and explainability are intentionally out of scope for this stage.

## Frontend

The Next.js frontend provides the user-facing shell for the future analysis platform:

- Landing page for responsible product positioning
- Future article analysis workspace
- Future prediction history
- Future model comparison page
- Future evaluation dashboard
- About page documenting scope and constraints

The frontend communicates with the backend through a configurable API base URL.

## Backend

The FastAPI backend is organized by responsibility:

- `api/` contains HTTP route definitions
- `core/` contains configuration, logging, and exception handling
- `db/` contains SQLAlchemy engine/session setup and declarative metadata
- `models/` will contain SQLAlchemy persistence models
- `schemas/` contains Pydantic request and response contracts
- `repositories/` will contain persistence access patterns
- `services/` will contain business workflow orchestration
- `nlp/` will contain text preprocessing and feature extraction components
- `ml/` will contain model interfaces, classifiers, and evaluation helpers
- `explainability/` will contain SHAP and other explanation workflows
- `utils/` contains shared implementation utilities

## Database

PostgreSQL is the planned persistence layer. The foundation includes:

- Environment-driven database URL configuration
- SQLAlchemy engine and session management
- Alembic migration configuration
- Persistent local PostgreSQL volume through Docker Compose

No prediction or model-result tables have been introduced yet.

## Future Components

### NLP Preprocessing

Future preprocessing components should be isolated under `backend/app/nlp/` and expose clear service interfaces. Expected responsibilities include text cleaning, normalization, tokenization, stop-word handling, vectorization support, and dataset transformation.

### Classical ML Baselines

Future baseline models should live under `backend/app/ml/`. They can include logistic regression, Naive Bayes, SVM, and tree-based classifiers. These should share a common interface for training, evaluation, persistence, and inference.

### Transformer Classification

Transformer-based classifiers should be added behind explicit model interfaces so they can be swapped, evaluated, and compared without changing API routes or persistence logic.

### Confidence Scoring

Confidence scores should be treated as model estimates, not truth guarantees. Future calibration logic can include probability calibration, confidence bands, and uncertainty reporting.

### SHAP Explainability

Explainability components should be separated under `backend/app/explainability/`. SHAP support can be added for compatible models with careful performance boundaries and transparent caveats.

### Model Comparison

The model comparison workflow should compare metrics across models, datasets, and evaluation runs. API contracts should avoid hard-coding one model family.

### Evaluation

Evaluation should support reproducible test splits and standard classification metrics such as accuracy, precision, recall, F1, ROC-AUC, calibration, and confusion matrices.

### Prediction History

Prediction history should be added only after the prediction API contract is designed. It should capture request metadata, model version, confidence, explanation references, and timestamps without storing secrets or unnecessary user data.

