"""Schemas do Banco de Q&A."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBase(BaseModel):
    pergunta: str = Field(min_length=1)
    resposta: str = Field(min_length=1)
    tags: str = ""
    categoria: str = ""
    ativo: bool = True


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeUpdate(BaseModel):
    pergunta: str | None = None
    resposta: str | None = None
    tags: str | None = None
    categoria: str | None = None
    ativo: bool | None = None


class KnowledgeOut(KnowledgeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
