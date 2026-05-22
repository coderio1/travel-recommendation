"""Application configuration.
Pydantic-settings loads environment variables and ensures it's
readability for whole the app on one place.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://travel:travel@db:5432/travel",
        description="SQLAlchemy URL using the psycopg (v3) driver.",
    )

    # JWT
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    # CORS — comma-separated list in env, parsed into list here
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS_ORIGINS env var into a list of origin strings."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — validaton made by pydantic only once per process."""
    return Settings()
