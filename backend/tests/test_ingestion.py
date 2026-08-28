from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models.article import ArticleLabel, ImportStatus, NewsArticle
from app.schemas.import_run import ColumnMapping, DatasetImportRequest
from app.services.ingestion import (
    AmbiguousLabelError,
    DatasetImportError,
    DatasetIngestionService,
    normalize_label,
    resolve_column_mapping,
)


def write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_label_normalization_accepts_internal_labels() -> None:
    assert normalize_label("real") == ArticleLabel.REAL
    assert normalize_label("FAKE") == ArticleLabel.FAKE


def test_numeric_label_requires_explicit_mapping() -> None:
    with pytest.raises(AmbiguousLabelError):
        normalize_label("1")

    assert normalize_label("1", {"1": ArticleLabel.REAL, "0": ArticleLabel.FAKE}) == ArticleLabel.REAL


def test_invalid_label_is_rejected() -> None:
    with pytest.raises(DatasetImportError):
        normalize_label("misleading")


def test_csv_column_mapping_uses_aliases_and_explicit_values() -> None:
    resolved = resolve_column_mapping(["headline", "article", "class", "publisher"])

    assert resolved["title"] == "headline"
    assert resolved["content"] == "article"
    assert resolved["label"] == "class"
    assert resolved["source_name"] == "publisher"

    explicit = resolve_column_mapping(
        ["my_title", "body", "truth_label"],
        ColumnMapping(title="my_title", content="body", label="truth_label"),
    )
    assert explicit["label"] == "truth_label"


def test_import_csv_tracks_counts_and_skips_duplicates(db_session: Session, tmp_path: Path) -> None:
    csv_path = tmp_path / "fixture.csv"
    write_csv(
        csv_path,
        "\n".join(
            [
                "headline,text,label,source,date,url",
                "Real title,Real body,REAL,Wire,2026-01-01,https://example.com/real",
                "Fake title,Fake body,FAKE,Outlet,2026-01-02,https://example.com/fake",
                "Fake title,Fake body,FAKE,Outlet,2026-01-02,https://example.com/fake",
                "Missing label,Body,,Outlet,2026-01-03,https://example.com/missing",
            ]
        ),
    )

    service = DatasetIngestionService(db_session, raw_data_dir=tmp_path)
    import_run = service.import_csv(
        DatasetImportRequest(dataset_name="synthetic-test", filename="fixture.csv")
    )

    articles = db_session.query(NewsArticle).all()
    assert import_run.status == ImportStatus.COMPLETED.value
    assert import_run.total_rows == 4
    assert import_run.successfully_imported_rows == 2
    assert import_run.duplicate_rows == 1
    assert import_run.invalid_rows == 1
    assert import_run.skipped_rows == 2
    assert len(articles) == 2
    assert {article.label for article in articles} == {"REAL", "FAKE"}


def test_import_csv_supports_explicit_numeric_label_mapping(db_session: Session, tmp_path: Path) -> None:
    csv_path = tmp_path / "numeric.csv"
    write_csv(
        csv_path,
        "\n".join(
            [
                "title,content,label",
                "A,B,1",
                "C,D,0",
            ]
        ),
    )

    service = DatasetIngestionService(db_session, raw_data_dir=tmp_path)
    import_run = service.import_csv(
        DatasetImportRequest(
            dataset_name="numeric-test",
            filename="numeric.csv",
            label_mapping={"1": ArticleLabel.REAL, "0": ArticleLabel.FAKE},
        )
    )

    assert import_run.successfully_imported_rows == 2
    assert import_run.invalid_rows == 0


def test_import_path_is_restricted_to_raw_directory(db_session: Session, tmp_path: Path) -> None:
    service = DatasetIngestionService(db_session, raw_data_dir=tmp_path)

    with pytest.raises(DatasetImportError):
        service.resolve_import_path("../secret.csv")

