from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.article import ArticleLabel
from app.repositories.article_repository import ArticleRepository
from app.schemas.article import NewsArticleResponse, PaginatedArticlesResponse

router = APIRouter(prefix="/articles")


@router.get("", response_model=PaginatedArticlesResponse)
async def list_articles(
    label: ArticleLabel | None = None,
    dataset: str | None = Query(default=None, max_length=255),
    source: str | None = Query(default=None, max_length=255),
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedArticlesResponse:
    repository = ArticleRepository(db)
    items, total = repository.list_articles(
        label=label,
        dataset=dataset,
        source=source,
        search=search,
        limit=limit,
        offset=offset,
    )
    return PaginatedArticlesResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{article_id}", response_model=NewsArticleResponse)
async def retrieve_article(
    article_id: UUID,
    db: Session = Depends(get_db),
) -> NewsArticleResponse:
    repository = ArticleRepository(db)
    article = repository.get(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    return article
