"""Schemas de Marca / Voz."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BrandVoiceUpdate(BaseModel):
    nome_assistente: str | None = None
    persona: str | None = None
    avatar_url: str | None = None
    assina_mensagens: bool | None = None
    descricao_empresa: str | None = None
    tom: str | None = None
    icp: str | None = None
    cta: str | None = None


class BrandVoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_assistente: str
    persona: str
    avatar_url: str
    assina_mensagens: bool
    descricao_empresa: str
    tom: str
    icp: str
    cta: str
