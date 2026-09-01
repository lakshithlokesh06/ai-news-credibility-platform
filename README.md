# AI News Credibility and Misinformation Detection Platform

Production-ready foundation for a full-stack AI/data-science platform for model-based news credibility and misinformation analysis.

The current implementation includes the application foundation plus dataset ingestion, canonical article persistence, preprocessing utilities, dataset statistics, classical ML training/evaluation, transformer fine-tuning support, model artifacts, model comparison, experiment tracking, explicit champion selection, model lifecycle management, model inference APIs, explainability APIs, persisted analysis history, human review, manual claim/evidence review, reviewed-production performance metrics, calibration diagnostics, error analysis, reference-profile generation, and model monitoring diagnostics. It does not implement authentication, LLMs, external fact-checking APIs, web scraping, RAG, source reputation scoring, claim verification, automatic retraining, or live news APIs.

## Purpose

This project is designed to grow into a platform that can analyze news headlines or articles using NLP, classical machine-learning baselines, transformer classifiers, confidence scoring, explainability, model comparison, and evaluation dashboards.

The system should provide model-based credibility and misinformation predictions based on learned textual patterns. It should not claim to independently prove whether a story is objectively true or false.

## Current Status

- Monorepo scaffold with separate frontend and backend applications
- FastAPI backend with health endpoints, configuration, logging, CORS, exceptions, SQLAlchemy session setup, Alembic, article models, import tracking, ingestion services, preprocessing services, dataset statistics, classical ML services, transformer services, experiment/lifecycle services, explainability services, history services, review services, manual evidence services, and monitoring services
- Next.js frontend shell with professional product navigation, live data overview, model registry, experiment tracking, evaluation dashboard, inference workspace, history dashboard, history detail views, manual evidence workspace, review queue, reviewed-production performance dashboard, and monitoring dashboards
- PostgreSQL development database via Docker Compose
- Backend tests for startup, health endpoints, ingestion, preprocessing, statistics, data APIs, classical training, transformer dispatch, artifacts, inference, explainability, analysis history, analytics, and model comparison
- Documentation for the current architecture, manual evidence workflow, and roadmap

## Technology Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, scikit-learn, numpy, joblib, SHAP, PyTorch, Hugging Face Transformers
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

## Production Readiness

The backend includes centralized environment validation, explicit production CORS checks, request IDs, security headers, structured request logging, in-process rate limits, bounded training/explainability concurrency, liveness/readiness endpoints, safe system metadata, and aggregate process metrics.

Operational endpoints:

- `GET /health` and `GET /api/v1/health` - process liveness
- `GET /api/v1/readiness` - database, schema, storage, and champion artifact readiness
- `GET /api/v1/system/info` - safe application metadata
- `GET /api/v1/system/metrics` - safe in-process request counters

Detailed deployment and security notes live in [docs/deployment.md](/Users/lakshithlokesh/Documents/ChatGPT/ai-news-credibility-platform/docs/deployment.md) and [docs/security.md](/Users/lakshithlokesh/Documents/ChatGPT/ai-news-credibility-platform/docs/security.md).

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
- `GET /api/v1/readiness`
- `GET /api/v1/system/info`
- `GET /api/v1/system/metrics`
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
- `POST /api/v1/ml/models/{training_run_id}/explain`
- `GET /api/v1/ml/model-comparison`
- `GET /api/v1/experiments`
- `GET /api/v1/experiments/{training_run_id}`
- `POST /api/v1/experiments/compare`
- `GET /api/v1/models/champion`
- `POST /api/v1/models/{training_run_id}/promote`
- `POST /api/v1/models/{training_run_id}/archive`
- `POST /api/v1/models/{training_run_id}/restore`
- `GET /api/v1/history`
- `GET /api/v1/history/statistics`
- `GET /api/v1/history/{analysis_id}`
- `POST /api/v1/history/{analysis_id}/claims`
- `GET /api/v1/history/{analysis_id}/claims`
- `GET /api/v1/history/{analysis_id}/evidence-summary`
- `PUT /api/v1/history/{analysis_id}/review`
- `DELETE /api/v1/history/{analysis_id}/review`
- `DELETE /api/v1/history/{analysis_id}`
- `PATCH /api/v1/claims/{claim_id}`
- `DELETE /api/v1/claims/{claim_id}`
- `POST /api/v1/claims/{claim_id}/evidence`
- `GET /api/v1/evidence/statistics`
- `PATCH /api/v1/evidence/{evidence_id}`
- `DELETE /api/v1/evidence/{evidence_id}`
- `GET /api/v1/reviews/queue`
- `GET /api/v1/reviews/statistics`
- `GET /api/v1/reviews/performance`
- `GET /api/v1/reviews/calibration`
- `GET /api/v1/reviews/errors`
- `GET /api/v1/monitoring`
- `GET /api/v1/monitoring/models/{training_run_id}`
- `POST /api/v1/monitoring/models/{training_run_id}/reference-profile`

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

## Explainability

The explanation flow is:

```text
Article
-> Selected Trained Model
-> Prediction
-> Probability / Confidence
-> SHAP / Feature Attribution
-> Influential Tokens/Phrases
-> Human-Readable Explanation
```

Explanations are available only through the dedicated `POST /api/v1/ml/models/{training_run_id}/explain` endpoint. Standard prediction does not run SHAP or attribution logic.

Explanation requests support bounded configuration for `max_items`, `method`, `max_transformer_length`, `max_evaluations`, and whether to include `REAL` or `FAKE` supporting evidence. The API returns normalized, frontend-friendly influential items with text, attribution score, supported class direction, rank, and offsets when they can be reconstructed reliably.

Classical strategy:

```text
TF-IDF -> Linear Model -> Feature Attribution / SHAP
```

For Logistic Regression, the default explanation uses the fitted TF-IDF vectorizer and classifier coefficients to compute local feature contributions for the exact input. Optional SHAP linear attribution is available for Logistic Regression. For calibrated Linear SVM, attributions refer to the underlying fitted linear decision function; sigmoid calibration affects probabilities, not which text features the SVM learned.

Transformer strategy:

```text
Tokenizer -> Fine-Tuned DistilBERT -> SHAP Text Attribution
```

Transformer explanations load the saved fine-tuned artifact and tokenizer for the selected completed training run. They use transformer-safe text composition, bounded SHAP text attribution, and conservative subword aggregation so fragments such as wordpieces can be displayed as readable tokens where safe.

SHAP and feature attribution explain model behavior; they do not verify factual claims. Influential words are not automatically false or true, and attribution reflects how the trained model responded to patterns learned from its dataset.

## Analysis History

The saved analysis flow is:

```text
Article
-> Selected Model
-> Prediction
-> Optional Explanation
-> Persisted Analysis Record
-> History
-> History Analytics
```

Prediction persistence is optional at the API level. `POST /api/v1/ml/models/{training_run_id}/predict` accepts `save_to_history: true` and returns `analysis_id` when a record is saved. Standard programmatic predictions remain non-persistent by default.

Explanations can attach to an existing saved analysis by passing `analysis_id` to `POST /api/v1/ml/models/{training_run_id}/explain`. The backend validates that the saved analysis belongs to the same training run and that the submitted title/content match the saved input. History detail pages read persisted prediction and explanation data; they do not rerun inference or SHAP.

Saved history is different from the training dataset. It stores user-submitted article text, prediction outputs, model metadata, and normalized explanation results in the configured PostgreSQL database. History list and statistics endpoints do not return full article bodies; full text is returned only from the individual detail endpoint.

Statistics are intentionally separated:

- Dataset statistics describe imported labeled training data.
- Evaluation metrics describe trained model performance on held-out labeled data.
- History analytics describe articles analyzed and saved by this application.

A history distribution such as 60% `FAKE` means 60% of saved analyses were classified as likely misinformation by selected models. It does not mean 60% of all news is fake.

## Human Review And Reviewed Production Metrics

Saved analyses can receive one current human review with a canonical `REAL` or `FAKE` verified label plus optional plain-text notes. A review never overwrites the original model prediction, probabilities, explanation, or history content.

Reviewed-production metrics are calculated only from saved analyses with explicit human-verified labels. They are separate from held-out validation/test metrics created during training. The review subsystem reports sample counts, review coverage, accuracy, precision, recall, F1, ROC-AUC when both classes and probabilities are available, a reviewed-analysis confusion matrix, calibration diagnostics, and error-analysis summaries.

For precision, recall, F1, and false-positive/false-negative labels, `FAKE` is treated as the positive class:

- False positive: model predicted `FAKE`, human-verified label is `REAL`
- False negative: model predicted `REAL`, human-verified label is `FAKE`

Metrics below `PERFORMANCE_MIN_REVIEWED_SAMPLES` are marked preliminary. The platform does not infer labels from confidence, explanation, source, model output, training labels, web results, or external APIs, and it never retrains or changes champion state automatically from review metrics.

## Manual Evidence And Claim Review

Saved analyses include a dedicated human evidence workspace:

```text
Saved Analysis
-> Manual Claim Identification
-> Manual Evidence Reference Entry
-> Human Evidence Assessment
-> Optional Human Review
```

Reviewers can identify claims from the saved article, add notes, record external reference URLs they found themselves, and classify each reference as `supports`, `contradicts`, `neutral`, or `unclear` for that claim. The backend validates URL shape and stores the URL and reviewer-entered metadata; it does not fetch pages, inspect OpenGraph data, crawl sites, scrape content, classify evidence, assign source trust scores, or decide the verified label.

Evidence summaries are workflow context only. They report counts, coverage, and assessment distribution so reviewers can see how much manual evidence has been recorded before assigning a human label. They are not credibility scores and are not mixed into model evaluation, monitoring drift, lifecycle promotion, or retraining. See [docs/evidence-review.md](/Users/lakshithlokesh/Documents/ChatGPT/ai-news-credibility-platform/docs/evidence-review.md) for the full workflow and limitations.

## Model Monitoring

The monitoring flow is:

```text
Completed Training Run
-> Reference Profile From Training Data
-> Saved Analysis Records
-> Input Drift / Prediction Drift / Confidence / Usage Diagnostics
-> Monitoring Dashboard
```

Reference profiles are generated for completed training runs and stored in `model_monitoring_profiles`. Classical profiles use the fitted TF-IDF artifact only for feature metadata; transformer profiles use model-independent text statistics. Monitoring does not load model weights for prediction, rerun inference, rerun SHAP, or retrain models.

Monitoring APIs are scoped to one training run at a time. They compare recent saved `analysis_records` for that run against the stored reference profile and return aggregate diagnostics only. Overview and detail responses avoid article bodies; history detail remains the only UI route that returns the full saved article content.

Current diagnostics include:

- input text/title length drift with PSI and KS statistics
- predicted `REAL`/`FAKE` distribution drift with Jensen-Shannon divergence
- confidence averages, low/high confidence rates, and confidence histograms
- usage volume, explanation generation rate, and last analyzed timestamp

Monitoring is operational telemetry, not truth verification. It cannot measure live production accuracy without labels, cannot verify claims, and does not automatically retrain or deploy models.

## Experiment Tracking And Lifecycle

Each `ml_training_runs` row is also treated as an experiment run. The experiment API exposes stored run metadata, dataset identifiers, text-composition and preprocessing configuration, hyperparameters, split configuration, validation/test metrics, artifact version/checksum, environment version summary, explainability support, monitoring availability, and lifecycle state.

Training execution status remains separate from lifecycle state:

- `status` tracks execution such as `training`, `completed`, or `failed`.
- `lifecycle_status` tracks model lifecycle such as `candidate`, `champion`, or `archived`.

New successful training runs become `candidate` by default. Failed and incomplete runs are not candidates. Existing completed runs are safely backfilled to candidate by the lifecycle migration.

Champion promotion is explicit. The champion is the application's preferred/default model, not a claim that it is objectively best in every setting. Promotion validates that the run completed, has validation and test metrics, has required artifact metadata, and has loadable/validated artifacts. Promoting a new champion demotes any existing champion in the same transaction, and a partial unique database index prevents multiple active champions. Lifecycle events record compact audit history for promotions, demotions, archive, and restore actions without introducing fake users.

Archived models remain available historically. Archiving does not delete training runs, metrics, artifacts, monitoring profiles, or saved analysis history. The active champion cannot be archived until another model is promoted. Restoring an archived model returns it to candidate status when its required metadata and artifacts are still valid.

Experiment comparison uses persisted validation or test metrics only. It supports accuracy, precision, recall, F1, and ROC-AUC with a configured primary metric and split. It flags limited comparability when selected runs differ in dataset identifiers, split configuration, or text-composition configuration. Monitoring metrics, confidence, and SHAP attributions are not folded into model-quality rankings.

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
- `/analyze` - model inference, automatic UI-side history saving, and explicit explanation workspace
- `/history` - saved analysis dashboard with filters, analytics, and summaries
- `/history/[analysisId]` - saved analysis detail with persisted prediction/explanation data, human review controls, and deletion
- `/history/[analysisId]/evidence` - manual claim and evidence review workspace for a saved analysis
- `/review` - focused queue for assigning human-verified labels to saved analyses
- `/models` - model registry and training action with model-family awareness
- `/experiments` - experiment tracking, comparison, and champion overview
- `/experiments/[trainingRunId]` - experiment detail, configuration, metrics, lifecycle events, and champion/archive actions
- `/evaluation` - validation/test metrics and model comparison dashboard across model families
- `/performance` - reviewed-production performance, calibration, and error-analysis dashboard
- `/monitoring` - model monitoring overview from saved analysis history
- `/monitoring/[trainingRunId]` - per-model monitoring diagnostics and reference-profile refresh
- `/about` - project information

## Roadmap

- Richer dataset import UI actions for server-local CSV files
- NLP preprocessing extensions for tokenization, optional stop-word handling, and feature extraction
- Additional transformer model options and tuning controls
- Additional confidence scoring and calibration workflows
- Richer explanation views and export workflows
- Optional alerting and export workflows for monitoring diagnostics
- Authentication and multi-user ownership
- Dataset provenance and richer experiment metadata
