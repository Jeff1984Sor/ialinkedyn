"""Schemas de Conversas e Mensagens."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageAuthor


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    autor: str
    conteudo: str
    criado_em: datetime


class MessageCreate(BaseModel):
    autor: MessageAuthor = MessageAuthor.LEAD
    conteudo: str = Field(min_length=1)


class ConversationCreate(BaseModel):
    lead_id: int
    canal: str = "linkedin"


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    canal: str
    criado_em: datetime


class ConversationDetalhe(ConversationOut):
    lead_nome: str = ""
    mensagens: list[MessageOut] = []


class ConversationResumo(ConversationOut):
    lead_nome: str = ""
    ultima_mensagem: str = ""
    ultima_em: datetime | None = None
