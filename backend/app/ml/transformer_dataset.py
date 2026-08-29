import random
from collections import Counter

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import ArticleLabel, NewsArticle
from app.ml.dataset import TrainingDatasetError
from app.ml.types import PreparedSample
from app.schemas.preprocessing import TextCompositionConfig
from app.services.preprocessing import EmptyTextError, compose_article_text, preprocess_for_transformer


LABEL2ID = {ArticleLabel.REAL.value: 0, ArticleLabel.FAKE.value: 1}
ID2LABEL = {0: ArticleLabel.REAL.value, 1: ArticleLabel.FAKE.value}


def set_transformer_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        from transformers import set_seed

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        set_seed(seed)
    except ImportError:
        return


class TransformerDatasetBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(
        self,
        *,
        dataset_names: list[str] | None,
        composition_config: TextCompositionConfig,
        minimum_samples_per_class: int = 6,
    ) -> list[PreparedSample]:
        statement = select(NewsArticle)
        if dataset_names:
            statement = statement.where(NewsArticle.dataset_name.in_(dataset_names))
        articles = list(self.db.execute(statement).scalars().all())
        if not articles:
            raise TrainingDatasetError("A labeled dataset must be imported before transformer training.")

        samples: list[PreparedSample] = []
        for article in articles:
            if article.label not in LABEL2ID:
                continue
            try:
                composed = compose_article_text(
                    title=article.title,
                    content=article.content,
                    config=composition_config,
                )
                processed = preprocess_for_transformer(composed)
            except EmptyTextError:
                continue
            samples.append(
                PreparedSample(
                    article_id=article.id,
                    text=processed,
                    label=article.label,
                    dataset_name=article.dataset_name,
                )
            )

        label_counts = Counter(sample.label for sample in samples)
        if set(label_counts) != set(LABEL2ID):
            raise TrainingDatasetError("Transformer training requires both REAL and FAKE classes.")
        for label, count in label_counts.items():
            if count < minimum_samples_per_class:
                raise TrainingDatasetError(
                    f"Class {label} has {count} samples; at least {minimum_samples_per_class} are required."
                )
        return samples


class EncodedTextDataset:
    def __init__(self, encodings: dict, labels: list[str]) -> None:
        self.encodings = encodings
        self.labels = [LABEL2ID[label] for label in labels]

    def __getitem__(self, index: int) -> dict:
        import torch

        item = {key: torch.tensor(value[index]) for key, value in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[index])
        return item

    def __len__(self) -> int:
        return len(self.labels)


def tokenize_texts(tokenizer, texts: list[str], max_sequence_length: int) -> dict:
    return tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=max_sequence_length,
    )

