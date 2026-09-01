# Demo Guide

This guide walks through a practical local demo of the AI News Credibility & Misinformation Detection Platform. Demo outputs should come from actual application execution; do not pre-populate fake metrics, fake SHAP results, or fake monitoring drift.

## 1. Start The Stack

```bash
cp .env.example .env
docker compose up --build
```

Open the frontend at `http://localhost:3000` and the API docs at `http://localhost:8000/docs` when docs are enabled.

## 2. Import Demo Data

The repository includes `data/raw/demo_synthetic_news.csv`, a compact synthetic dataset for exercising ingestion and training workflows.

This synthetic dataset is for demonstrating application functionality only and must not be used to evaluate real-world misinformation detection accuracy.

Import it through the backend API:

```bash
curl -X POST http://localhost:8000/api/v1/dataset-imports \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "synthetic-demo",
    "filename": "demo_synthetic_news.csv",
    "column_mapping": {
      "title": "title",
      "content": "content",
      "label": "label",
      "source_name": "source_name",
      "publication_date": "publication_date",
      "source_url": "source_url"
    }
  }'
```

Then visit `/data` to confirm article counts, label distribution, duplicate handling, and import status.

## 3. Train A Classical Model

Go to `/models` and use the training panel:

- Model: `Logistic Regression`
- Text: `Title + Content`

When the run completes, it appears in the model registry with validation/test metrics. These metrics are generated from the imported dataset and are not claims about real-world accuracy.

## 4. Optionally Train DistilBERT

Choose `DistilBERT Transformer` from the same training panel only if the machine has enough time, memory, and model files/cache access. Transformer training can be slow and may download Hugging Face model files when they are not already cached.

## 5. Promote A Champion

Open `/experiments`, choose a completed run, and use its experiment detail page to promote it. Champion status means the selected application default, not an automatic proof that the model is universally best.

## 6. Analyze An Article

Open `/analyze`, select the champion or another completed model, enter a headline or article body, and run analysis. The result shows:

- model prediction
- REAL/FAKE probabilities
- model confidence
- model metadata
- saved history status

## 7. Explain A Prediction

After prediction, request an explanation. SHAP and feature attribution show which learned text features influenced the model. Explanation is not factual evidence.

## 8. Review The Saved Analysis

Open `/history`, then a saved analysis detail page. Review the article, prediction, confidence, explanation, and evidence section. Assign a human-verified label only when a reviewer has made that judgment.

## 9. Add Claims And Evidence

From history detail or `/review`, open the evidence workspace. Manually add:

- claim text
- evidence URL
- optional title, publisher, date, excerpt, and reviewer note
- assessment: `supports`, `contradicts`, `neutral`, or `unclear`

The backend stores evidence URLs but does not fetch, crawl, scrape, preview, fact-check, or score them.

## 10. Inspect Performance And Monitoring

Use `/performance` after creating human-verified labels. It reports reviewed-production performance, calibration, and error analysis from saved predictions plus reviewer labels.

Use `/monitoring` to inspect behavior drift and confidence/usage diagnostics. Monitoring answers whether model/input behavior changed; it does not directly measure accuracy unless verified labels exist.
