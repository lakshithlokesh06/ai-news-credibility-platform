from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI News Credibility API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_news_credibility"
    backend_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="BACKEND_CORS_ORIGINS",
    )
    log_level: str = "INFO"
    docs_enabled: bool = True
    max_article_title_chars: int = Field(default=1000, ge=1, le=10000)
    max_article_content_chars: int = Field(default=20000, ge=100, le=500000)
    max_combined_article_chars: int = Field(default=24000, ge=100, le=510000)
    max_dataset_file_bytes: int = Field(default=50 * 1024 * 1024, ge=1024, le=2 * 1024 * 1024 * 1024)
    training_concurrency_limit: int = Field(default=1, ge=1, le=8)
    explanation_concurrency_limit: int = Field(default=1, ge=1, le=16)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    prediction_rate_limit: int = Field(default=120, ge=1, le=10000)
    explanation_rate_limit: int = Field(default=30, ge=1, le=10000)
    training_rate_limit: int = Field(default=10, ge=1, le=1000)
    mutation_rate_limit: int = Field(default=60, ge=1, le=10000)
    monitoring_rate_limit: int = Field(default=60, ge=1, le=10000)
    trusted_proxy_headers: bool = False
    review_note_max_chars: int = Field(default=1000, ge=1, le=5000)
    review_evidence_note_max_chars: int = Field(default=2000, ge=1, le=10000)
    performance_min_reviewed_samples: int = Field(default=20, ge=1, le=100000)
    calibration_default_bins: int = Field(default=10, ge=2, le=20)
    high_confidence_error_threshold: float = Field(default=0.90, ge=0.5, le=1.0)

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/") or value.endswith("/"):
            raise ValueError("API prefix must start with '/' and must not end with '/'.")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("Unsupported log level.")
        return normalized

    @field_validator("backend_cors_origins")
    @classmethod
    def validate_cors_origin_string(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        for origin in origins:
            if origin != "*":
                parsed = urlparse(origin)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    raise ValueError(f"Malformed CORS origin: {origin}")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def data_raw_dir(self) -> Path:
        return self.project_root / "data" / "raw"

    @property
    def trained_models_dir(self) -> Path:
        return self.project_root / "models" / "trained"

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if self.app_env == "production":
            if self.debug:
                raise ValueError("DEBUG must be disabled in production.")
            if not self.database_url:
                raise ValueError("DATABASE_URL is required in production.")
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origins are not allowed in production.")
            if not self.cors_origins:
                raise ValueError("Explicit CORS origins are required in production.")
            if self.docs_enabled:
                raise ValueError("DOCS_ENABLED should be false in production unless intentionally overridden.")
        if self.max_combined_article_chars < self.max_article_title_chars:
            raise ValueError("Combined article limit must be at least the title limit.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
