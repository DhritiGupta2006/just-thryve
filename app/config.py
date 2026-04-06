from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/greenflowcredit"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-to-a-long-random-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    environment: str = "development"
    log_level: str = "INFO"
    model_path: str = "app/ml/model.pkl"
    frontend_url: Optional[str] = None

    model_config = {"env_file": ".env", "protected_namespaces": ("settings_",)}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
