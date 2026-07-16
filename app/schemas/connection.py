"""Schemas de Conexão e limites de automação."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConexaoStatus(BaseModel):
    """Estado atual da conexão com o LinkedIn."""

    provider_configurado: str          # mock | unipile (vem do .env)
    provider_pronto: bool              # se o provedor real está utilizável
    conectado: bool
    nome: str = ""
    external_account_id: str = ""
    status: str = "DESCONECTADO"
    conectado_em: datetime | None = None
    aviso: str = ""


class ConectarRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=180, description="Apelido da conta no painel")


class AutomationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    limite_follows_dia: int
    limite_convites_dia: int
    limite_mensagens_dia: int
    modo_chat: str
    horario_inicio: int
    horario_fim: int


class AutomationUpdate(BaseModel):
    limite_follows_dia: int | None = Field(default=None, ge=0, le=100)
    limite_convites_dia: int | None = Field(default=None, ge=0, le=100)
    limite_mensagens_dia: int | None = Field(default=None, ge=0, le=200)
    modo_chat: str | None = Field(default=None, pattern="^(MANUAL|AUTO)$")
    horario_inicio: int | None = Field(default=None, ge=0, le=23)
    horario_fim: int | None = Field(default=None, ge=0, le=23)
