"""Resolve o prompt efetivo: customizado (banco) ou padrão."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.prompts import DEFAULTS
from app.models.prompt import PromptTemplate


def resolver(db: Session, chave: str) -> str:
    """Conteúdo efetivo do prompt (customizado se houver, senão o padrão)."""
    custom = db.scalar(select(PromptTemplate).where(PromptTemplate.chave == chave))
    if custom and custom.conteudo.strip():
        return custom.conteudo
    return DEFAULTS.get(chave, "")


def salvar(db: Session, chave: str, conteudo: str) -> PromptTemplate:
    item = db.scalar(select(PromptTemplate).where(PromptTemplate.chave == chave))
    if item is None:
        item = PromptTemplate(chave=chave, conteudo=conteudo)
        db.add(item)
    else:
        item.conteudo = conteudo
    db.commit()
    db.refresh(item)
    return item


def restaurar_padrao(db: Session, chave: str) -> None:
    """Apaga a customização -> volta a valer o padrão."""
    item = db.scalar(select(PromptTemplate).where(PromptTemplate.chave == chave))
    if item:
        db.delete(item)
        db.commit()


def eh_customizado(db: Session, chave: str) -> bool:
    item = db.scalar(select(PromptTemplate).where(PromptTemplate.chave == chave))
    return bool(item and item.conteudo.strip())
