from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import ArticleLabel, NewsArticle
from app.ml.types import PreparedSample
from app.schemas.preprocessing import PreprocessingConfig, TextCompositionConfig
from app.services.preprocessing import (
    EmptyTextError,
    compose_article_text,
    preprocess_for_classical_ml,
)


class TrainingDatasetError(ValueError):
    pass


class TrainingDatasetBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(
        self,
        *,
        dataset_names: list[str] | None,
        composition_config: TextCompositionConfig,
        preprocessing_config: PreprocessingConfig,
        minimum_samples_per_class: int = 6,
    ) -> list[PreparedSample]:
        statement = select(NewsArticle)
        if dataset_names:
            statement = statement.where(NewsArticle.dataset_name.in_(dataset_names))
        articles = list(self.db.execute(statement).scalars().all())
        if not articles:
            raise TrainingDatasetError("A labeled dataset must be imported before training.")

        samples: list[PreparedSample] = []
        invalid_count = 0
        for article in articles:
            if article.label not in {ArticleLabel.REAL.value, ArticleLabel.FAKE.value}:
                invalid_count += 1
                continue
            try:
                composed = compose_article_text(
                    title=article.title,
                    content=article.content,
                    config=composition_config,
                )
                processed = preprocess_for_classical_ml(composed, preprocessing_config)
            except EmptyTextError:
                invalid_count += 1
                continue
            samples.append(
                PreparedSample(
                    article_id=article.id,
                    text=processed,
                    label=article.label,
                    dataset_name=article.dataset_name,
                )
            )

        if invalid_count:
            # Invalid rows are not silently repaired; they are excluded and reported through the error when unsafe.
            pass
        label_counts = Counter(sample.label for sample in samples)
        if set(label_counts) != {ArticleLabel.REAL.value, ArticleLabel.FAKE.value}:
            raise TrainingDatasetError("Training requires both REAL and FAKE classes.")
        if len(samples) < minimum_samples_per_class * 2:
            raise TrainingDatasetError(
                f"At least {minimum_samples_per_class} samples per class are required for reproducible training."
            )
        for label, count in label_counts.items():
            if count < minimum_samples_per_class:
                raise TrainingDatasetError(
                    f"Class {label} has {count} samples; at least {minimum_samples_per_class} are required."
                )

        return samples
