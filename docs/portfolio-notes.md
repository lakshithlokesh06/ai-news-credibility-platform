# Portfolio Notes

## Short Project Description

AI News Credibility & Misinformation Detection Platform is a full-stack ML engineering project for news-text analysis, model comparison, explainability, monitoring, and responsible human review. It combines classical NLP baselines, transformer support, persisted analysis history, model lifecycle workflows, and manual evidence tracking while clearly separating model outputs from factual verification.

## Resume Bullet Suggestions

- Built a full-stack ML platform with Next.js, FastAPI, PostgreSQL, scikit-learn, Hugging Face Transformers, and SHAP for news credibility analysis, experiment tracking, model lifecycle management, and explainable inference.
- Implemented reproducible dataset ingestion, TF-IDF preprocessing, Logistic Regression, calibrated Linear SVM, DistilBERT training support, artifact-backed inference, model comparison, and monitoring diagnostics.
- Designed responsible review workflows with human-verified labels, reviewed-production performance, calibration/error analysis, manual claim tracking, and reviewer-entered evidence references without automated truth-verification claims.

## Interview Talking Points

- Classical baselines plus DistilBERT show the tradeoff between fast interpretable sparse-text models and contextual transformer representations.
- Probability calibration matters because downstream review, confidence filtering, and monitoring should not confuse raw scores with calibrated probabilities.
- SHAP is separated from evidence because attribution explains model behavior, while evidence is human-entered context about factual claims.
- Monitoring is separated from accuracy because drift and confidence shifts do not prove the model is right or wrong without verified labels.
- Verified production labels are needed to calculate reviewed-production accuracy, calibration, and error analysis from real saved analyses.
- Evidence URLs are not fetched automatically to avoid SSRF and accidental scraping concerns in a local portfolio app.
- Champion lifecycle is explicit so the default model is chosen deliberately rather than silently by recency or one metric.
- Production safeguards include request IDs, structured logging, bounded inputs, rate limits, concurrency controls, health/readiness endpoints, CORS validation, security headers, and controlled artifact paths.

## Recommended GitHub Topics

`machine-learning`, `natural-language-processing`, `misinformation-detection`, `fake-news-detection`, `fastapi`, `nextjs`, `transformers`, `shap`, `postgresql`, `mlops`
