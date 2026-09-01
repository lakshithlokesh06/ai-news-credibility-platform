# Changelog

## 1.0.0 - 2026-09-02

Initial portfolio-ready release of the AI News Credibility & Misinformation Detection Platform.

### Added

- Full-stack Next.js and FastAPI application structure with PostgreSQL persistence.
- Dataset ingestion, canonical article storage, duplicate handling, preprocessing, and dataset statistics.
- Classical ML training with TF-IDF, Logistic Regression, calibrated Linear SVM, reproducible splits, validation/test metrics, and artifact storage.
- DistilBERT training and inference support with lazy transformer dependency loading.
- Model prediction APIs with probabilities, model confidence, and optional saved analysis history.
- SHAP and feature-attribution explainability with persisted explanation snapshots.
- Model registry, experiment comparison, explicit champion/candidate/archive lifecycle, and lifecycle events.
- Monitoring reference profiles, input drift, prediction drift, confidence diagnostics, and usage windows.
- Human review with manually verified labels, reviewed-production performance, calibration diagnostics, and error analysis.
- Manual claim and evidence workspace with reviewer-entered URLs and supports/contradicts/neutral/unclear assessments.
- Production-readiness safeguards: request IDs, structured logging, input bounds, rate limits, concurrency controls, readiness checks, security headers, Docker Compose, and deployment docs.
- Synthetic demo dataset for exercising ingestion and training workflows without copyrighted or private data.

### Notes

- The platform is an ML-based analysis and evaluation system, not an automated truth engine.
- Verified labels, claims, and evidence assessments are human-entered.
- Evidence URLs are stored but not fetched, crawled, scraped, previewed, scored, or fact-checked automatically.
