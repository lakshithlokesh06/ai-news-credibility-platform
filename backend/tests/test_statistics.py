from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.article import DatasetImportRun, NewsArticle
from app.services.ingestion import build_duplicate_key, map_csv_record, resolve_column_mapping
from app.services.statistics import DatasetStatisticsService


def test_dataset_statistics_reflect_real_database_state(db_session: Session) -> None:
    started_at = datetime.now(UTC)
    import_run = DatasetImportRun(
        dataset_name="stats-fixture",
        source_filename="stats.csv",
        status="COMPLETED",
        total_rows=3,
        successfully_imported_rows=2,
        skipped_rows=1,
        invalid_rows=0,
        duplicate_rows=1,
        started_at=started_at,
        completed_at=started_at,
    )
    db_session.add(import_run)
    mapping = resolve_column_mapping(["title", "content", "label", "source"])

    rows = [
        {"title": "Real", "content": "Short article", "label": "REAL", "source": "Wire"},
        {"title": "", "content": "A much longer article body", "label": "FAKE", "source": "Blog"},
    ]
    for row in rows:
        mapped = map_csv_record(row, mapping)
        now = datetime.now(UTC)
        db_session.add(
            NewsArticle(
                title=mapped.title,
                content=mapped.content,
                label=mapped.label.value,
                source_name=mapped.source_name,
                dataset_name="stats-fixture",
                duplicate_key=build_duplicate_key("stats-fixture", mapped),
                import_run_id=import_run.id,
                created_at=now,
                updated_at=now,
            )
        )
    db_session.commit()

    stats = DatasetStatisticsService(db_session).calculate()

    assert stats.total_articles == 2
    assert stats.real_count == 1
    assert stats.fake_count == 1
    assert stats.real_percentage == 50.0
    assert stats.fake_percentage == 50.0
    assert stats.articles_missing_titles == 1
    assert stats.articles_missing_content == 0
    assert stats.duplicate_rows_detected == 1
    assert stats.dataset_distribution[0].name == "stats-fixture"

