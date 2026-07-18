"""Perfil completo de um lead — contatos, experiência e formação."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.lead import Lead
from app.models.user import User
from app.providers.factory import get_provider

router = APIRouter(prefix="/perfil", tags=["perfil"])


class Experiencia(BaseModel):
    empresa: str = ""
    cargo: str = ""
    periodo: str = ""
    local: str = ""


class Formacao(BaseModel):
    instituicao: str = ""
    curso: str = ""
    periodo: str = ""


class PerfilCompleto(BaseModel):
    nome: str = ""
    headline: str = ""
    sobre: str = ""
    localidade: str = ""
    linkedin_url: str = ""
    foto_url: str = ""
    seguidores: int | None = None
    conexoes: int | None = None
    # contatos (o que interessa para prospecção)
    emails: list[str] = []
    telefones: list[str] = []
    sites: list[str] = []
    # trajetória
    experiencias: list[Experiencia] = []
    formacoes: list[Formacao] = []
    habilidades: list[str] = []
    aviso: str = ""


def _texto(valor: Any) -> str:
    t = str(valor or "").strip()
    return "" if t.lower() in {"undefined", "null", "none"} else t


def _periodo(d: dict[str, Any]) -> str:
    inicio = d.get("start") or d.get("start_date") or {}
    fim = d.get("end") or d.get("end_date") or {}
    def fmt(x: Any) -> str:
        if isinstance(x, dict):
            ano = x.get("year") or ""
            mes = x.get("month") or ""
            return f"{mes}/{ano}" if mes and ano else str(ano or "")
        return _texto(x)
    a, b = fmt(inicio), fmt(fim)
    if a and b:
        return f"{a} - {b}"
    if a:
        return f"{a} - atual"
    return b


@router.get("/lead/{lead_id}", response_model=PerfilCompleto)
def perfil_do_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PerfilCompleto:
    """Busca no LinkedIn o perfil completo do lead (com contatos)."""
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    if not lead.linkedin_url:
        raise HTTPException(
            status_code=400,
            detail="Este lead não tem URL do LinkedIn para consultar.",
        )

    provider = get_provider(db)
    consultar = getattr(provider, "obter_perfil_completo", None)
    if consultar is None:
        raise HTTPException(
            status_code=501,
            detail="O provedor atual não traz o perfil completo. Configure o Unipile.",
        )

    d = consultar(lead.linkedin_url)

    # --- contatos ---
    emails: list[str] = []
    for e in d.get("emails") or []:
        valor = _texto(e.get("email") if isinstance(e, dict) else e)
        if valor:
            emails.append(valor)

    telefones: list[str] = []
    for t in d.get("phones") or []:
        valor = _texto(t.get("number") if isinstance(t, dict) else t)
        if valor:
            telefones.append(valor)

    sites: list[str] = []
    for w in (d.get("websites") or []) + (d.get("social_links") or []):
        valor = _texto(w.get("url") if isinstance(w, dict) else w)
        if valor:
            sites.append(valor)

    # --- trajetória ---
    experiencias = [
        Experiencia(
            empresa=_texto(x.get("company")),
            cargo=_texto(x.get("position") or x.get("title")),
            periodo=_periodo(x),
            local=_texto(x.get("location")),
        )
        for x in (d.get("work_experience") or [])
        if isinstance(x, dict)
    ]

    formacoes = [
        Formacao(
            instituicao=_texto(x.get("school") or x.get("institution")),
            curso=_texto(x.get("degree") or x.get("field_of_study")),
            periodo=_periodo(x),
        )
        for x in (d.get("education") or [])
        if isinstance(x, dict)
    ]

    habilidades = [
        _texto(s.get("name") if isinstance(s, dict) else s)
        for s in (d.get("skills") or [])
    ]
    habilidades = [h for h in habilidades if h][:15]

    nome = " ".join(
        p for p in [_texto(d.get("first_name")), _texto(d.get("last_name"))] if p
    ) or _texto(d.get("name")) or lead.nome

    aviso = ""
    if not emails and not telefones:
        aviso = (
            "O LinkedIn só mostra e-mail/telefone de quem já é sua conexão "
            "(ou de quem deixou público). Conecte-se para ver os contatos."
        )

    return PerfilCompleto(
        nome=nome,
        headline=_texto(d.get("headline")) or lead.headline,
        sobre=_texto(d.get("summary") or d.get("about")),
        localidade=_texto(d.get("location")),
        linkedin_url=lead.linkedin_url,
        foto_url=_texto(d.get("profile_picture_url")),
        seguidores=d.get("follower_count") if isinstance(d.get("follower_count"), int) else None,
        conexoes=d.get("connections_count") if isinstance(d.get("connections_count"), int) else None,
        emails=emails,
        telefones=telefones,
        sites=sites[:5],
        experiencias=experiencias[:8],
        formacoes=formacoes[:5],
        habilidades=habilidades,
        aviso=aviso,
    )
