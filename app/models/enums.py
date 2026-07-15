"""Enums do domínio (armazenados como String no banco)."""
from __future__ import annotations

from enum import Enum


class LeadStatus(str, Enum):
    NOVO = "NOVO"
    SEGUINDO = "SEGUINDO"
    CONVIDADO = "CONVIDADO"
    ABORDADO = "ABORDADO"
    RESPONDEU = "RESPONDEU"
    QUALIFICADO = "QUALIFICADO"
    GANHO = "GANHO"
    PERDIDO = "PERDIDO"


class MessageAuthor(str, Enum):
    LEAD = "LEAD"          # mensagem recebida do lead
    EU = "EU"              # mensagem enviada por nós
    IA_RASCUNHO = "IA_RASCUNHO"  # rascunho gerado pela IA (ainda não enviado)
