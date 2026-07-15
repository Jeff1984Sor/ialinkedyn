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
