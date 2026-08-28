from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.training import ClassicalModelType, MLTrainingRun, TrainingRunStatus
from app.ml.artifacts import ARTIFACT_VERSION, ArtifactStore
from app.ml.dataset import TrainingDatasetBuilder, TrainingDatasetError
from app.ml.evaluation import evaluate_classifier
from app.ml.features import create_tfidf_vectorizer
from app.ml.splitting import stratified_split
from app.ml.trainers import create_classifier
from app.repositories.training_run_repository import TrainingRunRepository
from app.schemas.ml import TrainingRunCreate


class TrainingService:
    def __init__(self, db: Session, artifact_base_dir: Path | None = None) -> None:
        self.db = db
        self.repository = TrainingRunRepository(db)
        self.artifact_store = ArtifactStore(artifact_base_dir)

    def train(self, config: TrainingRunCreate) -> MLTrainingRun:
        now = datetime.now(UTC)
        display_name = config.model_display_name or self._default_display_name(config.model_type, now)
        training_run = MLTrainingRun(
            model_type=config.model_type.value,
            model_display_name=display_name,
            status=TrainingRunStatus.TRAINING.value,
            preprocessing_config=config.preprocessing.model_dump(),
            text_composition_config=config.text_composition.model_dump(),
            tfidf_config=config.tfidf.model_dump(),
            model_hyperparameters=config.hyperparameters.model_dump(),
            split_config=config.split.model_dump(),
            random_seed=config.random_seed,
            dataset_identifiers=config.dataset_names or [],
            split_distributions={},
            started_at=now,
            created_at=now,
        )
        self.repository.add(training_run)
        self.db.commit()
        self.db.refresh(training_run)

        try:
            samples = TrainingDatasetBuilder(self.db).build(
                dataset_names=config.dataset_names,
                composition_config=config.text_composition,
                preprocessing_config=config.preprocessing,
            )
            split = stratified_split(samples, config.split, config.random_seed)
            vectorizer = create_tfidf_vectorizer(config.tfidf)
            train_features = vectorizer.fit_transform(split.train_texts)
            validation_features = vectorizer.transform(split.validation_texts)
            test_features = vectorizer.transform(split.test_texts)

            classifier, probability_method = create_classifier(config.model_type, config.hyperparameters)
            classifier.fit(train_features, split.train_labels)

            validation_metrics = evaluate_classifier(classifier, validation_features, split.validation_labels)
            test_metrics = evaluate_classifier(classifier, test_features, split.test_labels)
            dataset_identifiers = sorted({sample.dataset_name for sample in samples})

            artifact_payload = {
                "classifier": classifier,
                "vectorizer": vectorizer,
                "preprocessing_config": config.preprocessing.model_dump(),
                "text_composition_config": config.text_composition.model_dump(),
                "label_mapping": {"REAL": "REAL", "FAKE": "FAKE"},
                "training_config": config.model_dump(mode="json"),
            }
            artifact_path, artifact_checksum = self.artifact_store.save(
                training_run.id,
                artifact_payload,
                {
                    "training_run_id": str(training_run.id),
                    "model_type": config.model_type.value,
                    "model_display_name": display_name,
                    "probability_method": probability_method,
                    "validation_metrics": validation_metrics,
                    "test_metrics": test_metrics,
                },
            )

            training_run.status = TrainingRunStatus.COMPLETED.value
            training_run.train_count = len(split.train_labels)
            training_run.validation_count = len(split.validation_labels)
            training_run.test_count = len(split.test_labels)
            training_run.dataset_article_count = len(samples)
            training_run.dataset_identifiers = dataset_identifiers
            training_run.split_distributions = {
                **split.distributions,
                "all": dict(Counter(sample.label for sample in samples)),
            }
            training_run.validation_metrics = validation_metrics
            training_run.test_metrics = test_metrics
            training_run.artifact_path = artifact_path
            training_run.artifact_checksum = artifact_checksum
            training_run.artifact_version = ARTIFACT_VERSION
            training_run.probability_method = probability_method
            training_run.completed_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(training_run)
            return training_run
        except Exception as exc:
            self.db.rollback()
            failed_run = self.repository.get(training_run.id)
            if failed_run is not None:
                failed_run.status = TrainingRunStatus.FAILED.value
                failed_run.error_summary = str(exc)
                failed_run.completed_at = datetime.now(UTC)
                self.db.commit()
                self.db.refresh(failed_run)
                return failed_run
            raise

    @staticmethod
    def _default_display_name(model_type: ClassicalModelType, timestamp: datetime) -> str:
        readable_type = "Logistic Regression" if model_type == ClassicalModelType.LOGISTIC_REGRESSION else "Linear SVM"
        return f"{readable_type} {timestamp.strftime('%Y-%m-%d %H:%M')}"

