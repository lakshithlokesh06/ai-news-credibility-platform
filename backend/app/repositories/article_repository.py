from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.article import ArticleLabel, NewsArticle


class ArticleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, article: NewsArticle) -> NewsArticle:
        self.db.add(article)
        return article

    def get(self, article_id: UUID) -> NewsArticle | None:
        return self.db.get(NewsArticle, article_id)

    def duplicate_exists(self, dataset_name: str, duplicate_key: str) -> bool:
        statement = select(NewsArticle.id).where(
            NewsArticle.dataset_name == dataset_name,
            NewsArticle.duplicate_key == duplicate_key,
        )
        return self.db.execute(statement).first() is not None

    def list_articles(
        self,
        *,
        label: ArticleLabel | None = None,
        dataset: str | None = None,
        source: str | None = None,
        search: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[NewsArticle], int]:
        statement = select(NewsArticle)
        count_statement = select(func.count()).select_from(NewsArticle)

        filters = []
        if label is not None:
            filters.append(NewsArticle.label == label.value)
        if dataset:
            filters.append(NewsArticle.dataset_name == dataset)
        if source:
            filters.append(NewsArticle.source_name == source)
        if search:
            pattern = f"%{search}%"
            filters.append(or_(NewsArticle.title.ilike(pattern), NewsArticle.content.ilike(pattern)))

        if filters:
            statement = statement.where(*filters)
            count_statement = count_statement.where(*filters)

        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(
            statement.order_by(NewsArticle.created_at.desc()).limit(limit).offset(offset)
        ).scalars().all()
        return list(items), int(total)

