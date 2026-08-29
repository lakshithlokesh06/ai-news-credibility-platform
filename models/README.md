# Models Directory

This directory is reserved for trained model artifacts, checkpoints, experiment exports, and future explainability assets.

Model training stores generated artifacts under:

```text
models/trained/{training_run_id}/
```

Classical run directories contain:

- `model.joblib`: fitted TF-IDF vectorizer, fitted classifier, preprocessing configuration, text composition configuration, label mapping, and training configuration
- `metadata.json`: artifact version, checksum, model type, probability method, and evaluation summaries

Transformer run directories contain:

```text
models/trained/{training_run_id}/hf_model/
```

Transformer artifacts are written with Hugging Face `save_pretrained()` and include the local model configuration, tokenizer files, model weights such as `model.safetensors` or `pytorch_model.bin`, explicit `REAL`/`FAKE` label mappings, and supporting `metadata.json` with evaluation summaries and checksum validation.

Generated model binaries are intentionally excluded from git. The backend model registry stores safe metadata in PostgreSQL and loads artifacts only from this controlled directory.

Current model support:

- Logistic Regression with native probabilities
- Linear SVM with sigmoid calibration via `CalibratedClassifierCV`
- DistilBERT transformer fine-tuning with default base model `distilbert-base-uncased`

SHAP explainability assets are reserved for a future stage and are not implemented here.
