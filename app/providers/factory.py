"""Escolhe o provedor conforme a configuração salva no painel."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.providers.base import LinkedInProvider
from app.providers.mock import MockProvider
from app.services.config_service import get_provider_name


def get_provider(db: Session) -> LinkedInProvider:
    nome = get_provider_name(db)
    if nome == "unipile":
        # UnipileProvider entra na Fase 3 (provedor real).
        raise HTTPException(
            status_code=501,
            detail=(
                "Provedor Unipile ainda não implementado (Fase 3). "
                "Em Conexões, selecione o provedor 'Simulado (mock)' para desenvolver."
            ),
        )
    return MockProvider()
