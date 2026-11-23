from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # General
    environment: str = "development"
    project_name: str = "SmartKids – Smile & Grow"
    api_v1_prefix: str = "/api/v1"
    public_base_url: str = "http://localhost:8000"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    cors_origins: str = "http://localhost:8000"

    # Database
    postgres_db: str = "smartkids"
    postgres_user: str = "smartkids"
    postgres_password: str = "smartkids"
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_test_db: str = "smartkids_test"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"

    # Object storage (SeaweedFS, S3 API)
    s3_endpoint_url: str = "http://seaweedfs:8333"
    s3_access_key: str = "smartkids"
    s3_secret_key: str = "smartkids-secret"
    s3_region: str = "us-east-1"
    s3_bucket_public: str = "smartkids-public"
    s3_bucket_private: str = "smartkids-private"
    s3_presigned_expire_seconds: int = 900

    # Email
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    email_from: str = "no-reply@example.com"

    # Community health signal detection
    signal_window_days: int = 7
    signal_baseline_days: int = 28
    signal_min_reports: int = 4
    signal_ratio_threshold: float = 2.0
    aggregate_min_cell_size: int = 3

    @property
    def database_url(self) -> str:
        return self._db_url(self.postgres_db)

    @property
    def test_database_url(self) -> str:
        return self._db_url(self.postgres_test_db)

    def _db_url(self, name: str) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
