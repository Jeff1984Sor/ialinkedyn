"""Escolhe o provedor conforme a configuração salva no painel."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.providers.base import LinkedInProvider
from app.providers.mock import MockProvider
from app.providers.unipile import UnipileProvider
from app.services.config_service import get_provider_name, get_unipile


def get_provider(db: Session) -> LinkedInProvider:
    nome = get_provider_name(db)
    if nome == "unipile":
        dsn, api_key, account_id = get_unipile(db)
        return UnipileProvider(dsn=dsn, api_key=api_key, account_id=account_id)
    if nome == "mock":
        return MockProvider()
    raise HTTPException(status_code=400, detail=f"Provedor desconhecido: {nome}")
