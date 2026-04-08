from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://flux_user:flux_password@postgres:5432/flux_db"
    REDIS_URL: str = "redis://redis:6379"
    SECRET_KEY: str = "dev-secret-key-do-not-use-in-production-abc123xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OPENAI_API_KEY: str = "placeholder"
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()