"""Schemas dos prompts editáveis."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PromptOut(BaseModel):
    chave: str
    label: str
    conteudo: str
    padrao: str
    customizado: bool
    placeholders: list[str] = []


class PromptUpdate(BaseModel):
    conteudo: str = Field(min_length=1)


class MelhorarRequest(BaseModel):
    instrucao: str = Field(min_length=1, description="O que você quer mudar no prompt")
    # opcional: usar o texto que está na tela (ainda não salvo)
    conteudo_atual: str | None = None


class MelhorarResponse(BaseModel):
    sugestao: str
