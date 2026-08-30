# Architecture

## Current Foundation

The project is structured as a modular full-stack monorepo:

```text
Frontend -> FastAPI -> NLP/ML Services -> PostgreSQL
```

The current foundation includes the frontend application shell, backend API skeleton, database connectivity setup, Alembic migrations, canonical article persistence, dataset import tracking, CSV ingestion, preprocessing utilities, dataset statistics, classical ML training/evaluation, transformer fine-tuning and inference, model-family registry metadata, versioned artifacts, model comparison, explicit model explainability, persisted analysis history, and history analytics. Authentication, LLMs, RAG, external fact-checking APIs, web scraping, source reputation scoring, claim verification, and live news APIs are intentionally out of scope for this stage.

The current data pipeline is:

```text
CSV Dataset -> Validation/Mapping -> Canonical Articles -> PostgreSQL -> NLP Preprocessing -> Model Training
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

The current transformer pipeline is:

```text
Canonical Articles
-> Transformer-Safe Text Composition
-> Train/Validation/Test Split
-> Hugging Face Tokenizer
-> DistilBERT Fine-Tuning
-> Validation/Test Evaluation
-> Versioned Hugging Face Artifact
-> Transformer Inference
```

The current explanation pipeline is:

```text
Article
-> Selected Trained Model
-> Prediction
-> Probability / Confidence
-> SHAP / Feature Attribution
-> Influential Tokens/Phrases
-> Human-Readable Explanation
```

The current history persistence pipeline is:

```text
Analyze UI
-> Inference Service
-> Prediction
-> Optional Explainability Service
-> Persistence Service
-> PostgreSQL
-> History UI
```

## Frontend

The Next.js frontend provides the user-facing shell for the future analysis platform:

- Landing page for responsible product positioning
- Dataset overview page backed by live API data
- Inference and explanation workspace for completed classical and transformer models
- Saved analysis history, filtering, analytics, and detail views
- Model registry and training action with model-family awareness
- Evaluation dashboard backed by stored validation/test metrics across model families
- About page documenting scope and constraints

The frontend communicates with the backend through a configurable API base URL.

## Backend

The FastAPI backend is organized by responsibility:

- `api/` contains HTTP route definitions
- `core/` contains configuration, logging, and exception handling
- `db/` contains SQLAlchemy engine/session setup and declarative metadata
- `models/` contains SQLAlchemy persistence models
- `schemas/` contains Pydantic request and response contracts
- `repositories/` contains persistence access patterns for imports, articles, training runs, and analysis history
- `services/` contains business workflow orchestration, CSV ingestion, preprocessing, dataset statistics, and analysis-history persistence/analytics
- `nlp/` will contain future specialized NLP preprocessing and feature extraction components
- `ml/` contains dataset preparation, stratified splitting, TF-IDF feature extraction, classical trainers, transformer dataset/tokenization/device/artifact helpers, evaluation, inference, and comparison helpers
- `explainability/` contains explanation configuration, classical attribution, transformer SHAP attribution, SHAP adapters, token aggregation, normalization, and orchestration services
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
- `ml_training_runs`: auditable training-run records with model type, model family, base model name, status, preprocessing configuration, text composition configuration, TF-IDF configuration, transformer configuration, selected device, training duration, hyperparameters, split counts, dataset identifiers, validation/test metrics, artifact metadata, and failure information
- `analysis_records`: saved local analysis records with model metadata, submitted title/content, prediction probabilities, explanation status, normalized explanation JSON, and timestamps

No authentication or user-ownership tables have been introduced yet. The current installation is treated as a single-user/local application.

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

## Explainability

Explainability is separated from training, inference, routing, and persistence under `backend/app/explainability/`:

- `config.py`: structured explanation errors, shared limitations, and label helpers
- `classical.py`: TF-IDF linear-model feature attribution and optional Logistic Regression SHAP
- `transformer.py`: bounded SHAP text attribution for fine-tuned DistilBERT artifacts
- `shap_integration.py`: lazy SHAP imports and adapter helpers
- `phrase_aggregation.py`: conservative subword token aggregation
- `normalization.py`: direction-aware ranking and frontend response normalization
- `service.py`: training-run validation, prediction reuse, family dispatch, and response assembly

The backend exposes `POST /api/v1/ml/models/{training_run_id}/explain`. The endpoint validates that the selected training run exists, completed successfully, and has a controlled artifact path. It runs normal inference first, then computes bounded explanations. Explanation results do not affect training records and are persisted only when attached to a saved analysis.

Classical explanations use the exact fitted vectorizer and classifier from the artifact. Logistic Regression defaults to local coefficient-times-TF-IDF contributions, with optional SHAP linear attribution. Linear SVM explanations use the underlying fitted linear estimators inside the calibrated wrapper, so they describe the decision function rather than calibrated probability behavior.

Transformer explanations use the saved fine-tuned model, tokenizer, label mapping, and transformer-safe text composition from the selected run. SHAP text attribution is bounded by maximum sequence length and maximum evaluations. Raw SHAP structures remain internal; API responses expose normalized influential tokens or phrases grouped by direction.

Attribution direction is explicitly mapped to canonical `REAL` and `FAKE` labels. The frontend presents these as influences toward likely credible or likely misinformation. Scores explain model behavior for one input; they are not performance metrics and are not mixed into evaluation dashboards.

## Analysis History

Analysis history is intentionally separate from ML inference and explainability. The persistence service receives already-computed prediction or explanation responses and stores those exact normalized values, preventing saved history from disagreeing with what the user originally saw.

The `analysis_records` table stores:

- selected training run reference with `ON DELETE SET NULL`
- copied model family, model type, model name, and display name for historical resilience
- submitted title and content
- text composition mode
- predicted `REAL`/`FAKE` label
- probabilities, confidence, and probability method
- explanation status, method, explained class, normalized influential items, limitations, and generation timestamp
- created and updated timestamps

The current design stores normalized explanation data in JSON columns on `analysis_records` because each saved analysis has at most one current explanation snapshot. Raw SHAP objects, tensors, tokenizer objects, model artifacts, and large intermediate arrays are never persisted.

History APIs:

- `GET /api/v1/history`: paginated summaries with filters for prediction, model family, model type, training run, explanation availability, date range, and text search
- `GET /api/v1/history/statistics`: aggregate statistics derived from saved analyses
- `GET /api/v1/history/{analysis_id}`: full saved analysis detail, including article body and persisted explanation when present
- `DELETE /api/v1/history/{analysis_id}`: deletes only the saved analysis record

History list and statistics responses avoid returning full article bodies. The detail endpoint returns full content so users can review the original saved analysis. Opening a history detail does not load model artifacts, rerun inference, or rerun SHAP.

Dataset statistics, evaluation metrics, and history analytics are different concepts. Dataset statistics describe imported labeled training data. Evaluation metrics describe held-out model performance. History analytics describe aggregate characteristics of articles users analyzed and saved locally.

## Transformer Classifier

Transformer support is implemented as a model family alongside the classical baselines:

- `transformer_dataset.py`: builds canonical text samples, keeps explicit `REAL`/`FAKE` label mappings, and tokenizes after splitting
- `transformer_device.py`: selects `mps`, `cuda`, or `cpu` from an explicit preference
- `transformer_probabilities.py`: converts logits to stable softmax probabilities and confidence values
- `transformer_training.py`: lazily imports PyTorch and Hugging Face Transformers, fine-tunes DistilBERT, evaluates validation/test splits, and updates training-run metadata
- `transformer_artifacts.py`: saves and loads Hugging Face `save_pretrained()` artifacts with controlled paths and checksum metadata
- `transformer_inference.py`: loads completed transformer artifacts locally and returns predictions through the shared API schema

The default base model is `distilbert-base-uncased`, exposed through `model_type: "distilbert"`. Transformer training and inference use transformer-safe preprocessing, preserving casing, punctuation, sentence structure, and contextual wording after Unicode, HTML, and whitespace cleanup.

PyTorch and Hugging Face libraries are imported only inside transformer training/inference paths. Application startup should not download a model or load transformer weights.

Transformer probabilities are derived from the softmax of model logits. Confidence is the selected class probability. These values are model estimates learned from the imported dataset and should be interpreted with dataset bias, distribution shift, satire, opinion, and source coverage limitations in mind. The classifier is not an external fact-checker.

## Future Components

### NLP Preprocessing

Reusable preprocessing currently lives in `backend/app/services/preprocessing.py`. Future specialized NLP components can be isolated under `backend/app/nlp/` and expose clear service interfaces. Expected responsibilities include tokenization, optional stop-word handling, vectorization support, and dataset transformation.

### Additional Transformer Classification

Additional transformer classifiers can be added behind the existing model-family interfaces so they can be swapped, evaluated, and compared without changing API routes or persistence logic.

### Confidence Scoring

Confidence scores should be treated as model estimates, not truth guarantees. Current classical and transformer inference paths expose confidence only when probability estimates are available.

### Additional Explainability

Future explainability work can add richer visualization, cached model-specific explainer reuse, persisted explanation references, or additional methods while keeping the current `/explain` response contract stable.

### Model Comparison

The model comparison workflow compares metrics across models, datasets, evaluation runs, and model families. API contracts avoid hard-coding one model family.

### Evaluation

Evaluation should support reproducible test splits and standard classification metrics such as accuracy, precision, recall, F1, ROC-AUC, calibration, and confusion matrices.

### Authentication And Ownership

Authentication and per-user ownership can be added later. The current history schema avoids fake user IDs while keeping a clear place to introduce ownership in a future migration.
