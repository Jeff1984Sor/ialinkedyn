"""Conexões — configurar provedor/IA, vincular a conta e limites de automação.

TUDO é configurável pelo painel (nada de mexer no .env). Segredos ficam
criptografados com Fernet no banco.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import encrypt_token
from app.models.connection import AutomationSettings, LinkedInAccount
from app.models.user import User
from app.schemas.connection import (
    AutomationOut,
    AutomationUpdate,
    ConectarRequest,
    ConfigOut,
    ConfigUpdate,
    ConexaoStatus,
    TesteIAResult,
)
from app.services.config_service import (
    cifra,
    get_config,
    get_gemini,
    get_provider_name,
    get_unipile,
    mascarar,
)
from app.services.gemini import testar_chave

router = APIRouter(prefix="/connection", tags=["connection"])

_AVISO_MOCK = (
    "Provedor SIMULADO (mock): nenhuma conta real do LinkedIn está conectada — "
    "as ações são fingidas, sem risco e sem custo. Para valer, escolha o provedor "
    "Unipile aqui embaixo e cole a chave dele."
)
_AVISO_UNIPILE_SEM_CHAVE = (
    "Provedor Unipile selecionado, mas a chave de API ainda não foi preenchida aqui embaixo."
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


# ---------------------------------------------------------------- configuração


@router.get("/config", response_model=ConfigOut)
def obter_config(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConfigOut:
    cfg = get_config(db)
    _, unipile_key = get_unipile(db)
    gemini_key, gemini_model = get_gemini(db)
    return ConfigOut(
        linkedin_provider=cfg.linkedin_provider,
        unipile_dsn=cfg.unipile_dsn,
        unipile_key_configurada=bool(unipile_key),
        unipile_key_mascarada=mascarar(unipile_key),
        gemini_key_configurada=bool(gemini_key),
        gemini_key_mascarada=mascarar(gemini_key),
        gemini_model=gemini_model,
    )


@router.put("/config", response_model=ConfigOut)
def atualizar_config(
    dados: ConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConfigOut:
    """Salva a configuração. Campos de chave: omitir = manter, "" = apagar."""
    cfg = get_config(db)

    if dados.linkedin_provider is not None:
        cfg.linkedin_provider = dados.linkedin_provider
    if dados.unipile_dsn is not None:
        cfg.unipile_dsn = dados.unipile_dsn
    if dados.gemini_model is not None:
        cfg.gemini_model = dados.gemini_model or "gemini-2.5-flash"
    if dados.unipile_api_key is not None:
        cfg.unipile_api_key_cifrado = cifra(dados.unipile_api_key)
    if dados.gemini_api_key is not None:
        cfg.gemini_api_key_cifrado = cifra(dados.gemini_api_key)

    db.commit()
    return obter_config(db=db, _=user)


@router.post("/testar-ia", response_model=TesteIAResult)
def testar_ia(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TesteIAResult:
    """Faz uma chamada real ao Gemini para validar a chave salva."""
    api_key, model = get_gemini(db)
    try:
        resposta = testar_chave(api_key, model)
        return TesteIAResult(ok=True, mensagem=f"Funcionando! ({model}) → {resposta[:60]}")
    except HTTPException as e:
        return TesteIAResult(ok=False, mensagem=str(e.detail))


# ---------------------------------------------------------------- status/conta


@router.get("/status", response_model=ConexaoStatus)
def status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConexaoStatus:
    conta = _get_account(db)
    provider = get_provider_name(db)

    if provider == "mock":
        pronto, aviso = True, _AVISO_MOCK
    elif provider == "unipile":
        _, key = get_unipile(db)
        pronto = bool(key)
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
    provider = get_provider_name(db)

    if provider == "unipile":
        raise HTTPException(
            status_code=501,
            detail=(
                "Conexão real via Unipile ainda não implementada (Fase 3). "
                "Selecione o provedor 'Simulado (mock)' para desenvolver."
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


# ---------------------------------------------------------------- limites


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
