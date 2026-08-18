from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


INSECURE_JWT_SECRETS = {
    "development-only-jwt-secret-change-me",
    "replace-with-a-long-random-secret-at-least-32-chars",
}
INSECURE_TICKET_SECRETS = {
    "development-only-ticket-secret-change-me",
    "replace-with-an-independent-long-random-secret",
}


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
    jwt_secret: str = Field(
        default="development-only-jwt-secret-change-me",
        min_length=32,
    )
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=60, gt=0, le=1440)
    ticket_secret: str = Field(
        default="development-only-ticket-secret-change-me",
        min_length=32,
    )
    ticketmaster_api_key: str | None = None
    ticketmaster_base_url: AnyHttpUrl = "https://app.ticketmaster.com/discovery/v2/"
    ticketmaster_timeout_seconds: float = Field(default=10, gt=0, le=30)
    upload_directory: Path = Path(__file__).resolve().parents[2] / "uploads"
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, gt=0, le=20 * 1024 * 1024)


    @model_validator(mode="after")
    def normalize_asyncpg_ssl(self) -> "Settings":
        """Aceita a string de conexão que os provedores gerenciados entregam.

        Neon, Supabase e Render publicam a URL com `?sslmode=require`, que é a
        grafia do libpq. O asyncpg não conhece esse parâmetro e falha na conexão
        com `TypeError: connect() got an unexpected keyword argument 'sslmode'` —
        o primeiro erro de quem publica pela primeira vez. O equivalente aceito é
        `ssl`, então a chave é renomeada preservando o valor.
        """
        if "+asyncpg" not in self.database_url or "sslmode" not in self.database_url:
            return self

        partes = urlsplit(self.database_url)
        parametros = [
            ("ssl" if chave == "sslmode" else chave, valor)
            for chave, valor in parse_qsl(partes.query, keep_blank_values=True)
        ]
        self.database_url = urlunsplit(
            partes._replace(query=urlencode(parametros))
        )
        return self

    @model_validator(mode="after")
    def reject_development_secret_in_production(self) -> "Settings":
        if (
            self.environment == "production"
            and self.jwt_secret in INSECURE_JWT_SECRETS
        ):
            raise ValueError("JWT_SECRET must be configured in production")
        if (
            self.environment == "production"
            and self.ticket_secret in INSECURE_TICKET_SECRETS
        ):
            raise ValueError("TICKET_SECRET must be configured in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
