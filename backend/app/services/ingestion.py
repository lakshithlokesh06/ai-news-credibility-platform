import csv
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.article import ArticleLabel, DatasetImportRun, ImportStatus, NewsArticle
from app.repositories.article_repository import ArticleRepository
from app.repositories.import_run_repository import ImportRunRepository
from app.schemas.import_run import ColumnMapping, DatasetImportRequest
from app.services.preprocessing import compose_article_text


class DatasetImportError(ValueError):
    pass


class AmbiguousLabelError(DatasetImportError):
    pass


CANONICAL_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("title", "headline", "heading"),
    "content": ("content", "text", "article", "body"),
    "label": ("label", "class", "target"),
    "source_name": ("source_name", "source", "publisher", "outlet"),
    "author": ("author", "byline"),
    "publication_date": ("publication_date", "published_at", "publish_date", "date"),
    "source_url": ("source_url", "url", "link"),
    "external_id": ("external_id", "id", "article_id", "record_id"),
}


@dataclass(frozen=True)
class ImportableArticle:
    title: str | None
    content: str | None
    label: ArticleLabel
    source_name: str | None = None
    author: str | None = None
    publication_date: datetime | None = None
    source_url: str | None = None
    external_id: str | None = None


def normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def normalize_label(
    raw_label: Any,
    label_mapping: dict[str, ArticleLabel] | None = None,
) -> ArticleLabel:
    value = normalize_optional_text(raw_label)
    if value is None:
        raise DatasetImportError("Label is required.")

    if label_mapping is not None:
        for raw_value, label in label_mapping.items():
            if value.casefold() == raw_value.strip().casefold():
                return label
        raise DatasetImportError(f"Label value '{value}' is not present in the explicit label mapping.")

    if value in {"0", "1"}:
        raise AmbiguousLabelError("Numeric labels require an explicit mapping to REAL and FAKE.")

    normalized = value.strip().upper()
    if normalized in ArticleLabel.__members__:
        return ArticleLabel(normalized)

    raise DatasetImportError(f"Unsupported label '{value}'. Use REAL/FAKE or provide an explicit mapping.")


def resolve_column_mapping(
    available_columns: list[str],
    explicit_mapping: ColumnMapping | None = None,
) -> dict[str, str]:
    columns_by_normalized_name = {column.strip().casefold(): column for column in available_columns}
    resolved: dict[str, str] = {}

    explicit_values = explicit_mapping.model_dump(exclude_none=True) if explicit_mapping else {}
    for canonical_name, column_name in explicit_values.items():
        normalized_column_name = column_name.strip().casefold()
        if normalized_column_name not in columns_by_normalized_name:
            raise DatasetImportError(f"Mapped column '{column_name}' is not present in the CSV.")
        resolved[canonical_name] = columns_by_normalized_name[normalized_column_name]

    for canonical_name, aliases in CANONICAL_ALIASES.items():
        if canonical_name in resolved:
            continue
        for alias in aliases:
            if alias in columns_by_normalized_name:
                resolved[canonical_name] = columns_by_normalized_name[alias]
                break

    if "label" not in resolved:
        raise DatasetImportError("A label column is required.")
    if "title" not in resolved and "content" not in resolved:
        raise DatasetImportError("At least one title/headline or content/text column is required.")

    return resolved


def parse_publication_date(value: Any) -> datetime | None:
    normalized = normalize_optional_text(value)
    if normalized is None:
        return None

    iso_value = normalized.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        pass

    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized, date_format).replace(tzinfo=UTC)
        except ValueError:
            continue

    raise DatasetImportError(f"Invalid publication date '{normalized}'.")


def build_duplicate_key(dataset_name: str, article: ImportableArticle) -> str:
    composed_text = compose_article_text(title=article.title, content=article.content)
    payload = "|".join(
        [
            dataset_name.strip().casefold(),
            composed_text.strip().casefold(),
            (article.source_url or "").strip().casefold(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def map_csv_record(
    row: dict[str, Any],
    mapping: dict[str, str],
    label_mapping: dict[str, ArticleLabel] | None = None,
) -> ImportableArticle:
    article = ImportableArticle(
        title=normalize_optional_text(row.get(mapping.get("title", ""))),
        content=normalize_optional_text(row.get(mapping.get("content", ""))),
        label=normalize_label(row.get(mapping["label"]), label_mapping),
        source_name=normalize_optional_text(row.get(mapping.get("source_name", ""))),
        author=normalize_optional_text(row.get(mapping.get("author", ""))),
        publication_date=parse_publication_date(row.get(mapping.get("publication_date", ""))),
        source_url=normalize_optional_text(row.get(mapping.get("source_url", ""))),
        external_id=normalize_optional_text(row.get(mapping.get("external_id", ""))),
    )
    compose_article_text(title=article.title, content=article.content)
    return article


class DatasetIngestionService:
    def __init__(self, db: Session, raw_data_dir: Path | None = None) -> None:
        self.db = db
        self.raw_data_dir = (raw_data_dir or settings.data_raw_dir).resolve()
        self.article_repository = ArticleRepository(db)
        self.import_repository = ImportRunRepository(db)

    def resolve_import_path(self, filename: str) -> Path:
        requested_path = Path(filename)
        if requested_path.name != filename or requested_path.suffix.lower() != ".csv":
            raise DatasetImportError("Only CSV filenames inside data/raw are allowed.")
        candidate = (self.raw_data_dir / requested_path.name).resolve()
        if candidate.parent != self.raw_data_dir:
            raise DatasetImportError("Import path is outside the approved data directory.")
        if not candidate.exists() or not candidate.is_file():
            raise DatasetImportError(f"CSV file '{filename}' was not found in data/raw.")
        if candidate.stat().st_size > settings.max_dataset_file_bytes:
            raise DatasetImportError("CSV file exceeds the configured maximum import size.")
        return candidate

    def import_csv(self, request: DatasetImportRequest) -> DatasetImportRun:
        started_at = datetime.now(UTC)
        import_run = DatasetImportRun(
            dataset_name=request.dataset_name,
            source_filename=request.filename,
            status=ImportStatus.RUNNING.value,
            started_at=started_at,
        )
        self.import_repository.add(import_run)
        self.db.commit()
        self.db.refresh(import_run)

        invalid_messages: list[str] = []
        seen_duplicate_keys: set[str] = set()

        try:
            import_path = self.resolve_import_path(request.filename)
            with import_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                if reader.fieldnames is None:
                    raise DatasetImportError("CSV header row is required.")

                mapping = resolve_column_mapping(reader.fieldnames, request.column_mapping)

                for row_number, row in enumerate(reader, start=2):
                    import_run.total_rows += 1
                    try:
                        mapped_article = map_csv_record(row, mapping, request.label_mapping)
                        duplicate_key = build_duplicate_key(request.dataset_name, mapped_article)
                        if (
                            duplicate_key in seen_duplicate_keys
                            or self.article_repository.duplicate_exists(request.dataset_name, duplicate_key)
                        ):
                            import_run.duplicate_rows += 1
                            import_run.skipped_rows += 1
                            continue

                        now = datetime.now(UTC)
                        self.article_repository.add(
                            NewsArticle(
                                title=mapped_article.title,
                                content=mapped_article.content,
                                label=mapped_article.label.value,
                                source_name=mapped_article.source_name,
                                author=mapped_article.author,
                                publication_date=mapped_article.publication_date,
                                source_url=mapped_article.source_url,
                                dataset_name=request.dataset_name,
                                external_id=mapped_article.external_id,
                                duplicate_key=duplicate_key,
                                import_run_id=import_run.id,
                                created_at=now,
                                updated_at=now,
                            )
                        )
                        seen_duplicate_keys.add(duplicate_key)
                        import_run.successfully_imported_rows += 1
                    except DatasetImportError as exc:
                        import_run.invalid_rows += 1
                        import_run.skipped_rows += 1
                        if len(invalid_messages) < 5:
                            invalid_messages.append(f"row {row_number}: {exc}")

            import_run.status = ImportStatus.COMPLETED.value
            import_run.completed_at = datetime.now(UTC)
            import_run.error_summary = "; ".join(invalid_messages) or None
            self.db.commit()
            self.db.refresh(import_run)
            return import_run
        except (csv.Error, OSError, UnicodeDecodeError, DatasetImportError, SQLAlchemyError) as exc:
            self.db.rollback()
            failed_run = self.import_repository.get(import_run.id)
            if failed_run is not None:
                failed_run.status = ImportStatus.FAILED.value
                failed_run.completed_at = datetime.now(UTC)
                failed_run.error_summary = str(exc)
                self.db.commit()
                self.db.refresh(failed_run)
                return failed_run
            raise
