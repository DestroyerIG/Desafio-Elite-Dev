from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Elite Events API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://elite:elite@localhost:5432/elite"
    frontend_url: AnyHttpUrl = "http://localhost:3000"
    seed_password: str = Field(default="DevOnly123!", min_length=8)

    @property
    def debug(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()

