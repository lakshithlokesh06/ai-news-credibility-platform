from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.article import ArticleLabel, ImportStatus


class ColumnMapping(BaseModel):
    title: str | None = None
    content: str | None = None
    label: str | None = None
    source_name: str | None = None
    author: str | None = None
    publication_date: str | None = None
    source_url: str | None = None
    external_id: str | None = None


class DatasetImportRequest(BaseModel):
    dataset_name: str = Field(min_length=1, max_length=255)
    filename: str = Field(min_length=1, max_length=255)
    column_mapping: ColumnMapping | None = None
    label_mapping: dict[str, ArticleLabel] | None = None

    @field_validator("dataset_name")
    @classmethod
    def dataset_name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Dataset name is required.")
        return value

    @field_validator("filename")
    @classmethod
    def filename_must_be_safe_csv(cls, value: str) -> str:
        value = value.strip()
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("Only CSV filenames inside the approved data directory are allowed.")
        if not value.lower().endswith(".csv"):
            raise ValueError("Only CSV files are supported.")
        return value

    @field_validator("label_mapping")
    @classmethod
    def label_mapping_must_have_values(
        cls,
        value: dict[str, ArticleLabel] | None,
    ) -> dict[str, ArticleLabel] | None:
        if value is None:
            return value
        normalized: dict[str, ArticleLabel] = {}
        for raw_label, normalized_label in value.items():
            key = raw_label.strip()
            if not key:
                raise ValueError("Label mapping keys cannot be blank.")
            normalized[key] = normalized_label
        if not normalized:
            raise ValueError("Label mapping cannot be empty when provided.")
        return normalized


class DatasetImportRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_name: str
    source_filename: str
    status: ImportStatus
    total_rows: int
    successfully_imported_rows: int
    skipped_rows: int
    invalid_rows: int
    duplicate_rows: int
    started_at: datetime
    completed_at: datetime | None
    error_summary: str | None


class PaginatedImportRunsResponse(BaseModel):
    items: list[DatasetImportRunResponse]
    total: int
    limit: int
    offset: int

