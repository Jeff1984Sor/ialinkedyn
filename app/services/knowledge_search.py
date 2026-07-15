"""Busca de Q&A relevantes (v1: por sobreposição de palavras-chave).

Evolui para embeddings/semântico no futuro. Por ora, simples e eficaz.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeItem

_STOPWORDS = {
    "de", "da", "do", "a", "o", "e", "que", "com", "para", "por", "um", "uma",
    "os", "as", "no", "na", "em", "se", "meu", "minha", "voce", "você", "qual",
    "como", "quanto", "sobre", "the", "is", "to", "of", "and",
}


def _tokens(texto: str) -> set[str]:
    palavras = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", texto.lower())
    return {p for p in palavras if len(p) > 2 and p not in _STOPWORDS}


def buscar_relevantes(db: Session, pergunta: str, limite: int = 5) -> list[KnowledgeItem]:
    """Retorna os itens de Q&A mais parecidos com a pergunta."""
    itens = list(db.scalars(select(KnowledgeItem).where(KnowledgeItem.ativo.is_(True))))
    alvo = _tokens(pergunta)
    if not alvo:
        return itens[:limite]

    pontuados: list[tuple[int, KnowledgeItem]] = []
    for item in itens:
        base = _tokens(item.pergunta + " " + item.tags + " " + item.categoria)
        score = len(alvo & base)
        if score > 0:
            pontuados.append((score, item))

    pontuados.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in pontuados[:limite]]
