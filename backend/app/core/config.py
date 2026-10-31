import os
from functools import lru_cache


class Settings:
    APP_NAME: str = "REBT Suite API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rebt")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", '["http://localhost:3000"]').replace("'", '"')


@lru_cache
def get_settings():
    return Settings()
