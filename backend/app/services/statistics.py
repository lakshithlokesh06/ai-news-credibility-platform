from collections import Counter
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.article import ArticleLabel, DatasetImportRun, NewsArticle
from app.schemas.statistics import DatasetStatisticsResponse, DistributionItem
from app.services.preprocessing import compose_article_text


def _percentage(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((count / total) * 100, 2)


class DatasetStatisticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate(self) -> DatasetStatisticsResponse:
        articles = list(self.db.execute(select(NewsArticle)).scalars().all())
        total = len(articles)

        real_count = sum(1 for article in articles if article.label == ArticleLabel.REAL.value)
        fake_count = sum(1 for article in articles if article.label == ArticleLabel.FAKE.value)
        missing_titles = sum(1 for article in articles if not (article.title or "").strip())
        missing_content = sum(1 for article in articles if not (article.content or "").strip())

        lengths: list[int] = []
        for article in articles:
            try:
                lengths.append(len(compose_article_text(title=article.title, content=article.content)))
            except ValueError:
                continue

        dataset_counts = Counter(article.dataset_name for article in articles)
        source_counts = Counter(article.source_name or "Unknown" for article in articles)
        duplicate_rows_detected = int(
            self.db.execute(select(func.coalesce(func.sum(DatasetImportRun.duplicate_rows), 0))).scalar_one()
        )

        return DatasetStatisticsResponse(
            total_articles=total,
            real_count=real_count,
            fake_count=fake_count,
            real_percentage=_percentage(real_count, total),
            fake_percentage=_percentage(fake_count, total),
            articles_missing_titles=missing_titles,
            articles_missing_content=missing_content,
            average_article_length=round(sum(lengths) / len(lengths), 2) if lengths else None,
            median_article_length=float(median(lengths)) if lengths else None,
            minimum_article_length=min(lengths) if lengths else None,
            maximum_article_length=max(lengths) if lengths else None,
            duplicate_rows_detected=duplicate_rows_detected,
            dataset_distribution=[
                DistributionItem(name=name, count=count, percentage=_percentage(count, total))
                for name, count in dataset_counts.most_common()
            ],
            source_distribution=[
                DistributionItem(name=name, count=count, percentage=_percentage(count, total))
                for name, count in source_counts.most_common()
            ],
        )

