"""Identificação única de leads (evita abordar a mesma pessoa duas vezes).

A mesma pessoa aparece com URLs diferentes conforme a origem da busca:
    https://www.linkedin.com/in/fulano-123/
    https://www.linkedin.com/in/fulano-123?miniProfileUrn=urn%3Ali%3A...
Comparar a URL crua duplica o lead. Aqui normalizamos.
"""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.lead import Lead


def normalizar_url(url: str) -> str:
    """Reduz a URL do LinkedIn à sua forma canônica.

    'https://www.linkedin.com/in/fulano-123?miniProfileUrn=x' -> 'fulano-123'
    """
    valor = (url or "").strip()
    if not valor:
        return ""
    valor = valor.split("?")[0].split("#")[0].rstrip("/")
    if "/in/" in valor:
        valor = valor.split("/in/", 1)[1].split("/")[0]
    return valor.lower()


def url_canonica(url: str) -> str:
    """URL limpa para salvar no lead (sem parâmetros de rastreio)."""
    slug = normalizar_url(url)
    return f"https://www.linkedin.com/in/{slug}" if slug else ""


def achar_lead(db: Session, provider_id: str, linkedin_url: str) -> Lead | None:
    """Procura um lead existente pelo provider_id (preferido) ou pela URL
    normalizada — assim a mesma pessoa nunca vira dois leads."""
    pid = (provider_id or "").strip()
    if pid:
        lead = db.scalar(select(Lead).where(Lead.provider_id == pid))
        if lead:
            return lead

    slug = normalizar_url(linkedin_url)
    if not slug:
        return None

    # compara ignorando parâmetros: casa tanto a forma canônica quanto as antigas
    candidatos = db.scalars(
        select(Lead).where(
            or_(
                Lead.linkedin_url == url_canonica(linkedin_url),
                Lead.linkedin_url.ilike(f"%/in/{slug}%"),
            )
        )
    )
    for c in candidatos:
        if normalizar_url(c.linkedin_url) == slug:
            return c
    return None
