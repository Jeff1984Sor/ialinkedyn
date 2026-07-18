"""Rede — suas conexões, convites pendentes, saldo de InMail e crescimento."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.providers.factory import get_provider
from app.schemas.agent import PerfilEncontrado
from app.services.growth import detectar_aceites, sincronizar_conexoes

router = APIRouter(prefix="/rede", tags=["rede"])


class ConexoesResponse(BaseModel):
    total: int
    proximo_cursor: str = ""
    perfis: list[PerfilEncontrado] = []


class ConvitesPendentesResponse(BaseModel):
    total: int
    itens: list[dict] = []


class SaldoInMail(BaseModel):
    premium: int | None = None
    recruiter: int | None = None
    sales_navigator: int | None = None
    disponivel: bool = False
    aviso: str = ""


@router.get("/conexoes", response_model=ConexoesResponse)
def conexoes(
    limite: int = 100,
    cursor: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConexoesResponse:
    """Lista suas conexões do LinkedIn (para mandar mensagem no chat)."""
    provider = get_provider(db)
    listar = getattr(provider, "listar_relacoes", None)
    if listar is None:
        raise HTTPException(
            status_code=501,
            detail="O provedor atual não lista conexões. Configure o Unipile em Conexões.",
        )
    perfis, proximo = listar(limite=limite, cursor=cursor)
    return ConexoesResponse(
        total=len(perfis),
        proximo_cursor=proximo,
        perfis=[
            PerfilEncontrado(
                nome=p.nome,
                headline=p.headline,
                empresa=p.empresa,
                cargo=p.cargo,
                linkedin_url=p.linkedin_url,
                provider_id=p.provider_id,
                sobre=p.sobre,
            )
            for p in perfis
        ],
    )


@router.get("/convites-pendentes", response_model=ConvitesPendentesResponse)
def convites_pendentes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConvitesPendentesResponse:
    """Convites que você enviou e ainda não foram aceitos."""
    provider = get_provider(db)
    listar = getattr(provider, "listar_convites_enviados", None)
    if listar is None:
        return ConvitesPendentesResponse(total=0)
    itens = listar()
    return ConvitesPendentesResponse(total=len(itens), itens=itens)


@router.get("/inmail-saldo", response_model=SaldoInMail)
def inmail_saldo(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SaldoInMail:
    """Créditos de InMail (necessário para falar com quem não é conexão)."""
    provider = get_provider(db)
    consultar = getattr(provider, "saldo_inmail", None)
    if consultar is None:
        return SaldoInMail(aviso="Provedor atual não informa saldo de InMail.")
    try:
        d = consultar()
    except HTTPException as e:
        return SaldoInMail(aviso=str(e.detail))

    premium = d.get("premium")
    recruiter = d.get("recruiter")
    sales = d.get("sales_navigator")
    total = sum(v for v in [premium, recruiter, sales] if isinstance(v, int))
    return SaldoInMail(
        premium=premium,
        recruiter=recruiter,
        sales_navigator=sales,
        disponivel=total > 0,
        aviso=(
            ""
            if total > 0
            else "Sem créditos de InMail. É preciso LinkedIn Premium ou Sales Navigator."
        ),
    )


@router.post("/sincronizar-conexoes", response_model=dict)
def sincronizar(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Traz suas conexões do LinkedIn para o CRM."""
    return sincronizar_conexoes(db)


@router.post("/detectar-aceites", response_model=dict)
def detectar(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Roda agora a checagem de quem aceitou o convite (o worker também faz sozinho)."""
    return detectar_aceites(db)
