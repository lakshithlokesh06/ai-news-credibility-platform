import logging.config

from app.core.config import settings
from app.core.request_context import current_request_id


class RequestIdFilter:
    def filter(self, record) -> bool:
        record.request_id = getattr(record, "request_id", None) or current_request_id() or "-"
        return True


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {
                    "()": RequestIdFilter,
                },
            },
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] request_id=%(request_id)s %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["request_id"],
                }
            },
            "root": {
                "handlers": ["console"],
                "level": settings.log_level,
            },
        }
    )
