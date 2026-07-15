"""Escolhe o provedor conforme LINKEDIN_PROVIDER no .env."""
from __future__ import annotations

from app.core.config import settings
from app.providers.base import LinkedInProvider
from app.providers.mock import MockProvider


def get_provider() -> LinkedInProvider:
    if settings.linkedin_provider == "unipile":
        # UnipileProvider entra na Fase 3 (provedor real).
        # from app.providers.unipile import UnipileProvider
        # return UnipileProvider()
        raise NotImplementedError(
            "UnipileProvider ainda não implementado (Fase 3). Use LINKEDIN_PROVIDER=mock."
        )
    return MockProvider()
