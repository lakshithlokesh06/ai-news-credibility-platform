# Data Directory

This directory is reserved for local datasets and processed data used by NLP and ML workflows.

Large datasets and generated processed files are intentionally excluded from git. Keep only lightweight documentation, placeholders, and the small synthetic demo CSV in version control.

## Expected Dataset Location

Place source CSV files in:

```text
data/raw/
```

The backend import API only accepts filenames from this directory. It rejects absolute paths, parent-directory traversal, and non-CSV files.

## Supported CSV Concept

The importer expects a header row and one article per row. Source datasets may use different column names, so each CSV row is mapped into the platform's canonical article schema.

## Canonical Fields

- `title`: headline/title, optional when content exists
- `content`: article text/body, optional when title exists
- `label`: required, normalized to `REAL` or `FAKE`
- `source_name`: optional source, publisher, or outlet
- `author`: optional author/byline
- `publication_date`: optional date/timestamp
- `source_url`: optional metadata URL; the importer does not fetch it
- `dataset_name`: supplied in the import request
- `external_id`: optional original dataset identifier

## Mapping Behavior

Common aliases are detected automatically when unambiguous:

- `title`, `headline`, `heading`
- `content`, `text`, `article`, `body`
- `label`, `class`, `target`
- `source`, `source_name`, `publisher`, `outlet`
- `url`, `source_url`, `link`
- `date`, `published_at`, `publication_date`

You can also provide explicit `column_mapping` values in the API request when a dataset uses custom headers.

## Label Mapping Requirement

The importer accepts explicit `REAL` and `FAKE` text labels. Numeric labels such as `0` and `1` are rejected unless the request includes an explicit `label_mapping` that states which value means `REAL` and which means `FAKE`.

Labels are never inferred from article text.

## Example Import Workflow

1. Place a CSV file such as `example.csv` in `data/raw/`.
2. Start PostgreSQL with `docker compose up -d postgres`.
3. Run migrations from `backend/` with `alembic upgrade head`.
4. Start the backend with `uvicorn app.main:app --reload`.
5. Trigger the import:

```bash
curl -X POST http://localhost:8000/api/v1/dataset-imports \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "example-dataset",
    "filename": "example.csv",
    "column_mapping": {
      "title": "headline",
      "content": "text",
      "label": "label"
    }
  }'
```

The repository includes `data/raw/demo_synthetic_news.csv`, a small synthetic dataset for demonstrating ingestion and training workflows. It is not a benchmark and must not be used to evaluate real-world misinformation detection accuracy.

## Saved Analysis Data

Saved analysis history is not stored in this directory. When enabled through the analysis API or UI, submitted article titles and content are stored in the configured PostgreSQL database as `analysis_records`.

History analytics describe saved analyses created by local users of the application. They are separate from imported training-data statistics and model evaluation metrics.

## Monitoring Data

Model monitoring does not write files in this directory. Reference profiles and aggregate diagnostics are stored in PostgreSQL and derived from completed training runs plus saved `analysis_records`.

Monitoring overview/detail APIs avoid returning full article bodies. They report aggregate drift, confidence, and usage metrics for a training run and do not fetch external URLs, verify claims, rerun inference, rerun SHAP, or retrain models.
