from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "SENTRA API"
    DATABASE_URL: str = "postgresql+psycopg2://sentra:sentra@localhost:5432/sentra"
    JWT_SECRET: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 1440
    CORS_ORIGINS: str = "*"
    AUTO_CREATE_TABLES: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
