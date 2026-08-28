# Models Directory

This directory is reserved for trained model artifacts, checkpoints, experiment exports, and future explainability assets.

Classical ML training stores generated artifacts under:

```text
models/trained/{training_run_id}/
```

Each run directory contains:

- `model.joblib`: fitted TF-IDF vectorizer, fitted classifier, preprocessing configuration, text composition configuration, label mapping, and training configuration
- `metadata.json`: artifact version, checksum, model type, probability method, and evaluation summaries

Generated model binaries are intentionally excluded from git. The backend model registry stores safe metadata in PostgreSQL and loads artifacts only from this controlled directory.

Current baseline support:

- Logistic Regression with native probabilities
- Linear SVM with sigmoid calibration via `CalibratedClassifierCV`

Transformer models and SHAP explainability are future stages and are not implemented here.
