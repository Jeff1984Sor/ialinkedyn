"""Schemas dos agentes de IA."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ResponderRequest(BaseModel):
    conversation_id: int
    # Opcional: mensagem avulsa do lead (se não vier, usa a última da conversa)
    mensagem_lead: str | None = None
    salvar_rascunho: bool = True


class ResponderResponse(BaseModel):
    resposta: str
    qa_usadas: list[str] = []


class ProspectarRequest(BaseModel):
    # informe uma URL de perfil OU um texto livre descrevendo o perfil
    linkedin_url: str | None = None
    perfil_texto: str | None = None
    lead_id: int | None = None  # se quiser vincular a um lead existente


class ProspectarResponse(BaseModel):
    abordagem: str
    perfil_resumo: str = ""


# --- Busca no LinkedIn (Caçador) ---


class BuscarRequest(BaseModel):
    # Se vazio, usa o ICP cadastrado em Marca/Voz
    termo: str | None = None
    limite: int = Field(default=10, ge=1, le=50)


class PerfilEncontrado(BaseModel):
    nome: str = ""
    headline: str = ""
    empresa: str = ""
    cargo: str = ""
    linkedin_url: str = ""
    sobre: str = ""
    posts_recentes: list[str] = []
    ja_importado: bool = False


class BuscarResponse(BaseModel):
    termo_usado: str
    provider: str
    simulado: bool
    perfis: list[PerfilEncontrado] = []


class ImportarRequest(BaseModel):
    perfis: list[PerfilEncontrado]


class ImportarResponse(BaseModel):
    importados: int
    ignorados: int
    lead_ids: list[int] = []
