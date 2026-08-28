from pydantic import BaseModel


class DistributionItem(BaseModel):
    name: str
    count: int
    percentage: float


class DatasetStatisticsResponse(BaseModel):
    total_articles: int
    real_count: int
    fake_count: int
    real_percentage: float
    fake_percentage: float
    articles_missing_titles: int
    articles_missing_content: int
    average_article_length: float | None
    median_article_length: float | None
    minimum_article_length: int | None
    maximum_article_length: int | None
    duplicate_rows_detected: int
    dataset_distribution: list[DistributionItem]
    source_distribution: list[DistributionItem]

