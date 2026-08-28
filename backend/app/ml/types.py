from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PreparedSample:
    article_id: UUID
    text: str
    label: str
    dataset_name: str


@dataclass(frozen=True)
class SplitDataset:
    train_texts: list[str]
    validation_texts: list[str]
    test_texts: list[str]
    train_labels: list[str]
    validation_labels: list[str]
    test_labels: list[str]
    train_ids: list[UUID]
    validation_ids: list[UUID]
    test_ids: list[UUID]
    distributions: dict

