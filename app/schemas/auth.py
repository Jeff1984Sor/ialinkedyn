"""Schemas (Pydantic) de autenticação e usuário."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    usuario: str = Field(min_length=1, max_length=60)
    nome: str = Field(min_length=1, max_length=120)
    senha: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario: str
    nome: str
    ativo: bool
    criado_em: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
