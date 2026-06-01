from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    apollo_api_key: str
    apollo_base_url: str = "https://api.apollo.io"

    database_url: str
    redis_url: str = "redis://localhost:6379"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    cache_ttl_seconds: int = 3600         # 1h for company data
    alert_poll_interval_minutes: int = 60

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
