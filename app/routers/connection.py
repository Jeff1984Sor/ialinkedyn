"""Conexões — vincular a conta do LinkedIn e configurar limites de automação."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import encrypt_token
from app.models.connection import AutomationSettings, LinkedInAccount
from app.models.user import User
from app.schemas.connection import (
    AutomationOut,
    AutomationUpdate,
    ConectarRequest,
    ConexaoStatus,
)

router = APIRouter(prefix="/connection", tags=["connection"])

_AVISO_MOCK = (
    "Provedor SIMULADO (mock). Nenhuma conta real do LinkedIn está conectada — "
    "as ações são fingidas, sem risco e sem custo. Para conectar de verdade, "
    "contrate o Unipile e configure UNIPILE_API_KEY + LINKEDIN_PROVIDER=unipile no .env."
)
_AVISO_UNIPILE_SEM_CHAVE = (
    "LINKEDIN_PROVIDER=unipile, mas UNIPILE_API_KEY não está configurada no .env do servidor."
)


def _get_account(db: Session) -> LinkedInAccount | None:
    return db.scalar(select(LinkedInAccount).order_by(LinkedInAccount.id).limit(1))


def _get_or_create_settings(db: Session) -> AutomationSettings:
    cfg = db.scalar(select(AutomationSettings).limit(1))
    if cfg is None:
        cfg = AutomationSettings()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.get("/status", response_model=ConexaoStatus)
def status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConexaoStatus:
    conta = _get_account(db)
    provider = settings.linkedin_provider

    if provider == "mock":
        pronto, aviso = True, _AVISO_MOCK
    elif provider == "unipile":
        pronto = bool(settings.unipile_api_key)
        aviso = "" if pronto else _AVISO_UNIPILE_SEM_CHAVE
    else:
        pronto, aviso = False, f"Provedor desconhecido: {provider}"

    return ConexaoStatus(
        provider_configurado=provider,
        provider_pronto=pronto,
        conectado=bool(conta and conta.status == "CONECTADO"),
        nome=conta.nome if conta else "",
        external_account_id=conta.external_account_id if conta else "",
        status=conta.status if conta else "DESCONECTADO",
        conectado_em=conta.conectado_em if conta else None,
        aviso=aviso,
    )


@router.post("/conectar", response_model=ConexaoStatus)
def conectar(
    dados: ConectarRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConexaoStatus:
    """Vincula a conta do LinkedIn ao painel (via provedor)."""
    provider = settings.linkedin_provider

    if provider == "unipile":
        # Fase 3: aqui abriremos o fluxo real de conexão do Unipile.
        raise HTTPException(
            status_code=501,
            detail=(
                "Conexão real via Unipile ainda não implementada (Fase 3). "
                "Use LINKEDIN_PROVIDER=mock para desenvolver."
            ),
        )
    if provider != "mock":
        raise HTTPException(status_code=400, detail=f"Provedor desconhecido: {provider}")

    conta = _get_account(db)
    if conta is None:
        conta = LinkedInAccount()
        db.add(conta)

    conta.nome = dados.nome
    conta.provider = provider
    conta.external_account_id = "mock-account-1"
    conta.status = "CONECTADO"
    # mesmo no mock, guardamos o "token" já criptografado (mesmo caminho do real)
    conta.token_cifrado = encrypt_token("token-simulado")
    conta.conectado_em = datetime.now(timezone.utc)
    db.commit()

    return status(db=db, _=user)


@router.delete("/desconectar", response_model=ConexaoStatus)
def desconectar(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConexaoStatus:
    conta = _get_account(db)
    if conta:
        conta.status = "DESCONECTADO"
        conta.token_cifrado = ""
        conta.external_account_id = ""
        conta.conectado_em = None
        db.commit()
    return status(db=db, _=user)


@router.get("/settings", response_model=AutomationOut)
def obter_limites(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _get_or_create_settings(db)


@router.put("/settings", response_model=AutomationOut)
def atualizar_limites(
    dados: AutomationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cfg = _get_or_create_settings(db)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(cfg, campo, valor)
    db.commit()
    db.refresh(cfg)
    return cfg
