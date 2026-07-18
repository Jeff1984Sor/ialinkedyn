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
    # Conta escolhida na lista do provedor. Se vier, é salva na config.
    account_id: str | None = Field(default=None, description="ID da conta no provedor")
    # Apelido opcional; se vazio, usa o nome que veio do provedor.
    nome: str = Field(default="", max_length=180, description="Apelido da conta no painel")


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


class ConfigOut(BaseModel):
    """Configuração da ferramenta (segredos SEMPRE mascarados)."""

    # LinkedIn
    linkedin_provider: str
    unipile_dsn: str = ""
    unipile_account_id: str = ""
    unipile_key_configurada: bool = False
    unipile_key_mascarada: str = ""
    # IA
    ia_provider: str = "gemini"
    gemini_key_configurada: bool = False
    gemini_key_mascarada: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openai_key_configurada: bool = False
    openai_key_mascarada: str = ""
    openai_model: str = "gpt-4o"


class ConfigUpdate(BaseModel):
    """Omitir um campo = manter como está. Enviar "" = apagar."""

    linkedin_provider: str | None = Field(default=None, pattern="^(mock|unipile)$")
    unipile_dsn: str | None = None
    unipile_api_key: str | None = None
    unipile_account_id: str | None = None
    ia_provider: str | None = Field(default=None, pattern="^(gemini|openai)$")
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None


class TesteIAResult(BaseModel):
    ok: bool
    mensagem: str


class ContaDisponivel(BaseModel):
    """Conta já conectada no provedor (ex.: no painel do Unipile)."""

    id: str
    nome: str = ""
    tipo: str = ""
    status: str = ""


class ContasDisponiveis(BaseModel):
    provider: str
    contas: list[ContaDisponivel] = []
    erro: str = ""
