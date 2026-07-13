"""Configuração central do IALinkedyn (single-tenant).

Tudo vem do ambiente / arquivo .env. NUNCA hardcode de segredos.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "IALinkedyn"
    environment: str = "development"
    cors_origins: str = "http://localhost:3021"

    # Banco
    database_url: str = "postgresql+psycopg://ialinkedyn_user:senha@localhost:5432/ialinkedyn"

    # Auth (JWT simples)
    jwt_secret: str = "troque-por-um-segredo-forte"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Criptografia de tokens de terceiros (Fernet)
    fernet_key: str = ""

    # IA (Google Gemini)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Camada de conexão LinkedIn
    linkedin_provider: str = "mock"  # mock | unipile
    unipile_dsn: str = ""
    unipile_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS separadas por vírgula -> lista limpa."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Instância única das configurações (cacheada)."""
    return Settings()


settings = get_settings()
