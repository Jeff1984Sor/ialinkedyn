"""Schemas de Público-alvo e de Campanha."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import PerfilEncontrado


class AudienceBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    termo: str = Field(min_length=1, description="Palavras-chave da busca no LinkedIn")
    descricao: str = ""
    ativo: bool = True


class AudienceCreate(AudienceBase):
    pass


class AudienceUpdate(BaseModel):
    nome: str | None = None
    termo: str | None = None
    descricao: str | None = None
    ativo: bool | None = None


class AudienceOut(AudienceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime


# ---------------------------------------------------------------- campanha


class CampanhaRequest(BaseModel):
    """Enfileira abordagens personalizadas para os perfis selecionados."""

    perfis: list[PerfilEncontrado]
    audience_id: int | None = None
    # CONVITE (padrão, para quem não é conexão) ou MENSAGEM (chat direto)
    tipo: str = Field(default="CONVITE", pattern="^(CONVITE|MENSAGEM)$")


class CampanhaResponse(BaseModel):
    enfileirados: int
    leads_criados: int
    ja_abordados: int = 0
    limite_diario: int = 0
    restante_hoje: int = 0
    aviso: str = ""


class TarefaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    tipo: str
    mensagem: str
    status: str
    erro: str
    enviado_em: datetime | None
    criado_em: datetime
    lead_nome: str = ""


class FilaStatus(BaseModel):
    pendentes: int
    enviados_hoje: int
    erros: int
    limite_diario: int
    restante_hoje: int
    dentro_do_horario: bool
    horario: str = ""
    tarefas: list[TarefaOut] = []
