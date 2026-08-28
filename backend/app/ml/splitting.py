from collections import Counter

from sklearn.model_selection import train_test_split

from app.ml.types import PreparedSample, SplitDataset
from app.schemas.ml import SplitConfig


def _distribution(labels: list[str]) -> dict[str, int]:
    return dict(Counter(labels))


def stratified_split(
    samples: list[PreparedSample],
    config: SplitConfig,
    random_seed: int,
) -> SplitDataset:
    texts = [sample.text for sample in samples]
    labels = [sample.label for sample in samples]
    ids = [sample.article_id for sample in samples]

    train_texts, temp_texts, train_labels, temp_labels, train_ids, temp_ids = train_test_split(
        texts,
        labels,
        ids,
        test_size=config.validation_ratio + config.test_ratio,
        random_state=random_seed,
        stratify=labels,
    )
    test_fraction_of_temp = config.test_ratio / (config.validation_ratio + config.test_ratio)
    validation_texts, test_texts, validation_labels, test_labels, validation_ids, test_ids = train_test_split(
        temp_texts,
        temp_labels,
        temp_ids,
        test_size=test_fraction_of_temp,
        random_state=random_seed,
        stratify=temp_labels,
    )

    return SplitDataset(
        train_texts=train_texts,
        validation_texts=validation_texts,
        test_texts=test_texts,
        train_labels=train_labels,
        validation_labels=validation_labels,
        test_labels=test_labels,
        train_ids=train_ids,
        validation_ids=validation_ids,
        test_ids=test_ids,
        distributions={
            "train": _distribution(train_labels),
            "validation": _distribution(validation_labels),
            "test": _distribution(test_labels),
        },
    )

