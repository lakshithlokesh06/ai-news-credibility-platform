# Architecture

## Current Foundation

The project is structured as a modular full-stack monorepo:

```text
Frontend -> FastAPI -> NLP/ML Services -> PostgreSQL
```

The current foundation includes the frontend application shell, backend API skeleton, database connectivity setup, Alembic migrations, canonical article persistence, dataset import tracking, CSV ingestion, preprocessing utilities, dataset statistics, classical ML training/evaluation, model registry metadata, versioned artifacts, model comparison, and classical-model inference. Transformer inference, SHAP explainability, LLMs, external fact-checking APIs, web scraping, and prediction history are intentionally out of scope for this stage.

The current data pipeline is:

```text
CSV Dataset -> Validation/Mapping -> Canonical Articles -> PostgreSQL -> NLP Preprocessing -> Future Model Training
```

The current classical ML pipeline is:

```text
Canonical Articles
-> Train/Validation/Test Split
-> Classical NLP Preprocessing
-> TF-IDF
-> Logistic Regression / Linear SVM
-> Validation/Test Evaluation
-> Versioned Artifact
-> Classical Inference
```

## Frontend

The Next.js frontend provides the user-facing shell for the future analysis platform:

- Landing page for responsible product positioning
- Dataset overview page backed by live API data
- Classical inference workspace for completed baseline models
- Future prediction history
- Classical model registry and simple baseline training action
- Evaluation dashboard backed by stored validation/test metrics
- About page documenting scope and constraints

The frontend communicates with the backend through a configurable API base URL.

## Backend

The FastAPI backend is organized by responsibility:

- `api/` contains HTTP route definitions
- `core/` contains configuration, logging, and exception handling
- `db/` contains SQLAlchemy engine/session setup and declarative metadata
- `models/` contains SQLAlchemy persistence models
- `schemas/` contains Pydantic request and response contracts
- `repositories/` contains persistence access patterns
- `services/` contains business workflow orchestration, CSV ingestion, preprocessing, and statistics
- `nlp/` will contain future specialized NLP preprocessing and feature extraction components
- `ml/` contains dataset preparation, stratified splitting, TF-IDF feature extraction, classical trainers, evaluation, artifacts, inference, and comparison helpers
- `explainability/` will contain SHAP and other explanation workflows
- `utils/` contains shared implementation utilities

## Database

PostgreSQL is the planned persistence layer. The foundation includes:

- Environment-driven database URL configuration
- SQLAlchemy engine and session management
- Alembic migration configuration
- Persistent local PostgreSQL volume through Docker Compose

Current persistence tables:

- `news_articles`: canonical imported article records with `REAL`/`FAKE` labels, optional metadata, duplicate keys, and import-run references
- `dataset_import_runs`: auditable import-run records with status, row counts, duplicate counts, invalid counts, start/completion timestamps, and error summaries
- `ml_training_runs`: auditable training-run records with model type, status, preprocessing configuration, text composition configuration, TF-IDF configuration, hyperparameters, split counts, dataset identifiers, validation/test metrics, artifact metadata, and failure information

No prediction-history or model-result tables have been introduced yet.

## Canonical Article Schema

Datasets can use different source column names, but ingestion maps rows to a stable internal schema:

- `title`: headline or title, nullable when content is present
- `content`: article text/body/content, nullable when title is present
- `label`: required internal label, currently `REAL` or `FAKE`
- `source_name`: optional source, publisher, or outlet
- `author`: optional author or byline
- `publication_date`: optional parsed timestamp
- `source_url`: optional metadata URL; it is never fetched by the importer
- `dataset_name`: required import dataset identifier
- `external_id`: optional original dataset row/article identifier
- `duplicate_key`: deterministic hash for duplicate handling
- `import_run_id`: optional link to the import run that created the record

The importer requires an explicit label field and never infers labels from text.

## Dataset Import Architecture

CSV imports are handled by `DatasetIngestionService`, not directly in API routes. The service:

- Resolves filenames only inside `data/raw/`
- Reads CSV headers and rows with `csv.DictReader`
- Applies explicit or alias-based column mappings
- Normalizes labels to `REAL` or `FAKE`
- Requires explicit mappings for numeric labels such as `0` and `1`
- Validates that each row has a label and at least title or content
- Normalizes optional metadata without fetching external URLs
- Detects duplicate rows by dataset and duplicate key
- Records import totals, imported rows, skipped rows, invalid rows, duplicate rows, and error summaries

Supported column aliases include names such as `title`, `headline`, `text`, `content`, `article`, `label`, `class`, `author`, `source`, `url`, and `date`.

## Preprocessing

Preprocessing is separated from ingestion and model training.

Classical ML preprocessing supports:

- Unicode normalization
- HTML tag removal
- Whitespace normalization
- URL normalization or removal
- Optional lowercasing
- Conservative punctuation spacing
- Empty-text validation

Transformer-safe preprocessing is intentionally minimal. It normalizes Unicode, removes HTML markup, and normalizes whitespace while preserving casing, punctuation, sentence structure, and contextual wording.

Article text composition is explicit through `title_only`, `content_only`, and `title_and_content` profiles.

## Classical ML Baselines

Classical ML code is modular under `backend/app/ml/`:

- `dataset.py`: builds training samples from canonical articles and validates class balance
- `splitting.py`: deterministic stratified train/validation/test splitting
- `features.py`: TF-IDF vectorizer construction
- `trainers.py`: Logistic Regression and calibrated Linear SVM classifier factories
- `evaluation.py`: binary classification metrics
- `artifacts.py`: controlled artifact persistence, checksum validation, and safe loading
- `training_service.py`: lifecycle orchestration and database updates
- `inference.py`: model loading and prediction using stored preprocessing/composition configs
- `comparison.py`: metric-based comparison across completed training runs

The TF-IDF vectorizer is fitted only on training text. Validation and test splits use `transform` on the fitted vectorizer. Validation metrics can inform model selection; test metrics are stored separately and should remain untouched during fitting and selection.

Logistic Regression exposes native `predict_proba`. Linear SVM is wrapped with sigmoid `CalibratedClassifierCV`; the calibration method and CV count are stored so probability outputs are not confused with raw SVM decision scores.

Artifacts live under `models/trained/{training_run_id}/` and contain fitted sklearn objects plus safe metadata. The loader accepts only controlled relative artifact paths and validates expected files, artifact version, and checksum before loading.

## Future Components

### NLP Preprocessing

Reusable preprocessing currently lives in `backend/app/services/preprocessing.py`. Future specialized NLP components can be isolated under `backend/app/nlp/` and expose clear service interfaces. Expected responsibilities include tokenization, optional stop-word handling, vectorization support, and dataset transformation.

### Transformer Classification

Transformer-based classifiers should be added behind explicit model interfaces so they can be swapped, evaluated, and compared without changing API routes or persistence logic.

### Confidence Scoring

Confidence scores should be treated as model estimates, not truth guarantees. Current classical inference exposes confidence only when genuine probability estimates are available.

### SHAP Explainability

Explainability components should be separated under `backend/app/explainability/`. SHAP support can be added for compatible models with careful performance boundaries and transparent caveats.

### Model Comparison

The model comparison workflow should compare metrics across models, datasets, and evaluation runs. API contracts should avoid hard-coding one model family.

### Evaluation

Evaluation should support reproducible test splits and standard classification metrics such as accuracy, precision, recall, F1, ROC-AUC, calibration, and confusion matrices.

### Prediction History

Prediction history should be added only after the prediction API contract is designed. It should capture request metadata, model version, confidence, explanation references, and timestamps without storing secrets or unnecessary user data.
