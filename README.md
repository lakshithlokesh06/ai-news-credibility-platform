# AI News Credibility and Misinformation Detection Platform

Production-ready foundation for a full-stack AI/data-science platform for model-based news credibility and misinformation analysis.

The current implementation includes the application foundation plus dataset ingestion, canonical article persistence, preprocessing utilities, dataset statistics, classical ML training/evaluation, transformer fine-tuning support, model artifacts, model comparison, and model inference APIs. It does not implement SHAP explainability, LLMs, external fact-checking APIs, web scraping, RAG, or prediction history.

## Purpose

This project is designed to grow into a platform that can analyze news headlines or articles using NLP, classical machine-learning baselines, transformer classifiers, confidence scoring, explainability, model comparison, and evaluation dashboards.

The system should provide model-based credibility and misinformation predictions based on learned textual patterns. It should not claim to independently prove whether a story is objectively true or false.

## Current Status

- Monorepo scaffold with separate frontend and backend applications
- FastAPI backend with health endpoints, configuration, logging, CORS, exceptions, SQLAlchemy session setup, Alembic, article models, import tracking, ingestion services, preprocessing services, dataset statistics, classical ML services, and transformer services
- Next.js frontend shell with professional product navigation, live data overview, model registry, evaluation dashboard, and inference workspace
- PostgreSQL development database via Docker Compose
- Backend tests for startup, health endpoints, ingestion, preprocessing, statistics, data APIs, classical training, transformer dispatch, artifacts, inference, and model comparison
- Documentation for the current architecture and roadmap

## Technology Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, scikit-learn, numpy, joblib, PyTorch, Hugging Face Transformers
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
- `POST /api/v1/ml/training-runs`
- `GET /api/v1/ml/training-runs`
- `GET /api/v1/ml/training-runs/{training_run_id}`
- `POST /api/v1/ml/models/{training_run_id}/predict`
- `GET /api/v1/ml/model-comparison`

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

## Classical ML Training

The current training pipeline is:

```text
Canonical Articles
-> Train/Validation/Test Split
-> Classical NLP Preprocessing
-> TF-IDF
-> Logistic Regression / Linear SVM
-> Evaluation
-> Versioned Artifact
-> Inference
```

Training is synchronous for this stage and uses only canonical `news_articles` records. It validates that a real imported dataset exists, both `REAL` and `FAKE` classes are present, each class has enough samples, composed text is non-empty, and stratified splitting can proceed safely.

Default split ratios are 70% training, 15% validation, and 15% test. Splitting is deterministic with a stored random seed and stratified by label. The TF-IDF vectorizer is fitted only on the training split; validation and test data are transformed with that fitted vectorizer to prevent leakage.

Supported models:

- Logistic Regression with `predict_proba`
- Linear SVM wrapped in sigmoid `CalibratedClassifierCV`, with the calibration method recorded in metadata

Validation metrics and untouched test metrics are stored separately. Metrics include accuracy, precision, recall, F1, ROC-AUC where probabilities are available, confusion matrix, class-level metrics, and support.

## Model Artifacts

Trained artifacts are saved under:

```text
models/trained/{training_run_id}/
```

Each artifact directory includes the fitted TF-IDF vectorizer, classifier, preprocessing configuration, text composition configuration, label mapping, training configuration, metadata, and checksum validation. Model binaries are not stored in PostgreSQL and are excluded from Git.

The artifact loader only accepts relative artifact paths inside the controlled `models/trained/` directory and rejects traversal or incomplete artifacts.

## Classical Inference

The inference API uses the exact preprocessing and text-composition configuration stored with the selected completed training run. Responses include predicted label, `REAL` probability, `FAKE` probability, confidence when valid probabilities exist, and the probability method.

Inference responses are model-based classifications from learned dataset patterns. They are not independent verification of factual truth.

## Transformer Training

The transformer training pipeline is:

```text
Canonical News Articles
-> Transformer-Safe Text
-> Stratified Split
-> Hugging Face Tokenizer
-> DistilBERT
-> Fine-Tuning
-> Validation
-> Final Test Evaluation
-> Versioned Hugging Face Artifact
-> Inference
```

The default transformer model is `distilbert-base-uncased` with explicit binary labels:

```text
REAL -> 0
FAKE -> 1
```

Transformer support is integrated through the existing training and prediction APIs. Use `model_type: "distilbert"` with `POST /api/v1/ml/training-runs` to create a transformer training run. Optional transformer configuration includes `model_name`, `max_sequence_length`, `batch_size`, `learning_rate`, `epochs`, `weight_decay`, `evaluation_strategy`, and `device_preference`.

PyTorch and Hugging Face Transformers are imported lazily by the transformer training and inference services. FastAPI startup does not download a model or load transformer weights. Real transformer training will download the configured Hugging Face model unless it is already available in the local cache.

Device selection supports `auto`, `mps`, `cuda`, and `cpu`. CPU training is expected to be slow, and small numeric differences can occur across devices.

Transformer probabilities are derived from the softmax of final logits. `confidence` is the selected class probability. These scores remain model estimates, not proof of factual truth.

Classical and transformer model families intentionally coexist. Classical models are fast, transparent baselines with lightweight artifacts; transformers can learn richer contextual patterns at higher compute and artifact cost.

## Transformer Artifacts

Transformer artifacts are saved under:

```text
models/trained/{training_run_id}/hf_model/
```

Each transformer run stores Hugging Face `save_pretrained()` output plus safe metadata, label mappings, evaluation summaries, and checksum validation. Large model binaries are excluded from Git.

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
- `/analyze` - model inference workspace for completed classical and transformer runs
- `/history` - future prediction history
- `/models` - model registry and training action with model-family awareness
- `/evaluation` - validation/test metrics and model comparison dashboard across model families
- `/about` - project information

## Roadmap

- Richer dataset import UI actions for server-local CSV files
- NLP preprocessing extensions for tokenization, optional stop-word handling, and feature extraction
- Additional transformer model options and tuning controls
- Additional confidence scoring and calibration workflows
- SHAP-based explainability for model outputs where appropriate
- Prediction history and audit trail
- Dataset provenance and richer experiment metadata
