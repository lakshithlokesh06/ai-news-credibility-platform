from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.article import ArticleLabel


class NewsArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    content: str | None
    label: ArticleLabel
    source_name: str | None
    author: str | None
    publication_date: datetime | None
    source_url: str | None
    dataset_name: str
    external_id: str | None
    import_run_id: UUID | None
    created_at: datetime
    updated_at: datetime


class PaginatedArticlesResponse(BaseModel):
    items: list[NewsArticleResponse]
    total: int
    limit: int
    offset: int


class ArticleQueryParams(BaseModel):
    label: ArticleLabel | None = None
    dataset: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=255)
    search: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

