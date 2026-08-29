from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from app.ml.evaluation import evaluate_classifier
from app.ml.splitting import stratified_split
from app.ml.transformer_artifacts import TRANSFORMER_ARTIFACT_VERSION, TransformerArtifactStore
from app.ml.transformer_dataset import (
    ID2LABEL,
    LABEL2ID,
    EncodedTextDataset,
    TransformerDatasetBuilder,
    set_transformer_seed,
    tokenize_texts,
)
from app.ml.transformer_device import select_device
from app.schemas.ml import TrainingRunCreate


class TransformerDependencyError(RuntimeError):
    pass


class _PredictionAdapter:
    def __init__(self, probabilities: np.ndarray) -> None:
        self.probabilities = probabilities
        self.classes_ = np.array(["REAL", "FAKE"])

    def predict(self, _features: Any) -> list[str]:
        return [ID2LABEL[int(index)] for index in np.argmax(self.probabilities, axis=1)]

    def predict_proba(self, _features: Any) -> np.ndarray:
        return self.probabilities


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=1, keepdims=True)


class TransformerTrainingService:
    def __init__(self, db, artifact_base_dir: Path | None = None) -> None:
        self.db = db
        self.artifact_store = TransformerArtifactStore(artifact_base_dir)

    def train(self, training_run, config: TrainingRunCreate) -> None:
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
        except ImportError as exc:
            raise TransformerDependencyError(
                "Transformer training requires transformers and torch. Install backend transformer dependencies."
            ) from exc

        set_transformer_seed(config.random_seed)
        device = select_device(config.transformer.device_preference)
        samples = TransformerDatasetBuilder(self.db).build(
            dataset_names=config.dataset_names,
            composition_config=config.text_composition,
        )
        split = stratified_split(samples, config.split, config.random_seed)

        tokenizer = AutoTokenizer.from_pretrained(config.transformer.model_name)
        train_encodings = tokenize_texts(tokenizer, split.train_texts, config.transformer.max_sequence_length)
        validation_encodings = tokenize_texts(tokenizer, split.validation_texts, config.transformer.max_sequence_length)
        test_encodings = tokenize_texts(tokenizer, split.test_texts, config.transformer.max_sequence_length)

        train_dataset = EncodedTextDataset(train_encodings, split.train_labels)
        validation_dataset = EncodedTextDataset(validation_encodings, split.validation_labels)
        test_dataset = EncodedTextDataset(test_encodings, split.test_labels)

        model = AutoModelForSequenceClassification.from_pretrained(
            config.transformer.model_name,
            num_labels=2,
            label2id=LABEL2ID,
            id2label=ID2LABEL,
        )
        model.to(torch.device(device))

        output_dir = self.artifact_store.base_dir / str(training_run.id) / "training-output"
        args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=config.transformer.epochs,
            per_device_train_batch_size=config.transformer.batch_size,
            per_device_eval_batch_size=config.transformer.batch_size,
            learning_rate=config.transformer.learning_rate,
            weight_decay=config.transformer.weight_decay,
            eval_strategy=config.transformer.evaluation_strategy,
            save_strategy="no",
            report_to=[],
            seed=config.random_seed,
            dataloader_num_workers=0,
            use_mps_device=(device == "mps"),
        )
        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=validation_dataset,
            tokenizer=tokenizer,
        )
        trainer.train()

        validation_predictions = trainer.predict(validation_dataset)
        test_predictions = trainer.predict(test_dataset)
        validation_probabilities = _softmax(np.asarray(validation_predictions.predictions))
        test_probabilities = _softmax(np.asarray(test_predictions.predictions))
        validation_metrics = evaluate_classifier(
            _PredictionAdapter(validation_probabilities),
            validation_probabilities,
            split.validation_labels,
        )
        test_metrics = evaluate_classifier(
            _PredictionAdapter(test_probabilities),
            test_probabilities,
            split.test_labels,
        )

        artifact_path, artifact_checksum = self.artifact_store.save(
            training_run.id,
            model,
            tokenizer,
            {
                "training_run_id": str(training_run.id),
                "model_family": "transformer",
                "model_type": config.model_type.value,
                "base_model_name": config.transformer.model_name,
                "label2id": LABEL2ID,
                "id2label": ID2LABEL,
                "transformer_config": config.transformer.model_dump(),
                "text_composition_config": config.text_composition.model_dump(),
                "validation_metrics": validation_metrics,
                "test_metrics": test_metrics,
                "device_used": device,
            },
        )

        training_run.train_count = len(split.train_labels)
        training_run.validation_count = len(split.validation_labels)
        training_run.test_count = len(split.test_labels)
        training_run.dataset_article_count = len(samples)
        training_run.dataset_identifiers = sorted({sample.dataset_name for sample in samples})
        training_run.split_distributions = {
            **split.distributions,
            "all": dict(Counter(sample.label for sample in samples)),
        }
        training_run.validation_metrics = validation_metrics
        training_run.test_metrics = test_metrics
        training_run.artifact_path = artifact_path
        training_run.artifact_checksum = artifact_checksum
        training_run.artifact_version = TRANSFORMER_ARTIFACT_VERSION
        training_run.probability_method = "softmax_logits"
        training_run.device_used = device
        training_run.training_duration_seconds = (
            datetime.now(tz=training_run.started_at.tzinfo) - training_run.started_at
        ).total_seconds()

