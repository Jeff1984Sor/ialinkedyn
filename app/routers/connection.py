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
    get_openai,
    get_provider_name,
    get_unipile,
    mascarar,
)
from app.services.ia import testar as testar_ia_service

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
    _, unipile_key, account_id = get_unipile(db)
    gemini_key, gemini_model = get_gemini(db)
    openai_key, openai_model = get_openai(db)
    return ConfigOut(
        linkedin_provider=cfg.linkedin_provider,
        unipile_dsn=cfg.unipile_dsn,
        unipile_account_id=account_id,
        unipile_key_configurada=bool(unipile_key),
        unipile_key_mascarada=mascarar(unipile_key),
        ia_provider=cfg.ia_provider or "gemini",
        gemini_key_configurada=bool(gemini_key),
        gemini_key_mascarada=mascarar(gemini_key),
        gemini_model=gemini_model,
        openai_key_configurada=bool(openai_key),
        openai_key_mascarada=mascarar(openai_key),
        openai_model=openai_model,
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
        cfg.unipile_dsn = dados.unipile_dsn.strip()
    if dados.unipile_account_id is not None:
        cfg.unipile_account_id = dados.unipile_account_id.strip()
    if dados.unipile_api_key is not None:
        cfg.unipile_api_key_cifrado = cifra(dados.unipile_api_key.strip())

    if dados.ia_provider is not None:
        cfg.ia_provider = dados.ia_provider
    if dados.gemini_model is not None:
        cfg.gemini_model = dados.gemini_model or "gemini-2.5-flash"
    if dados.gemini_api_key is not None:
        chave = dados.gemini_api_key.strip()
        if chave.startswith("sk-"):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Essa é uma chave da OpenAI (começa com 'sk-'), não do Gemini. "
                    "Troque o Motor de IA para OpenAI, ou cole uma chave do Google "
                    "(começa com 'AIza')."
                ),
            )
        cfg.gemini_api_key_cifrado = cifra(chave)
    if dados.openai_model is not None:
        cfg.openai_model = dados.openai_model or "gpt-4o"
    if dados.openai_api_key is not None:
        chave = dados.openai_api_key.strip()
        if chave.startswith("AIza"):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Essa é uma chave do Google Gemini (começa com 'AIza'), não da "
                    "OpenAI. Troque o Motor de IA para Gemini, ou cole uma chave da "
                    "OpenAI (começa com 'sk-')."
                ),
            )
        cfg.openai_api_key_cifrado = cifra(chave)

    db.commit()
    return obter_config(db=db, _=user)


@router.post("/testar-ia", response_model=TesteIAResult)
def testar_ia(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TesteIAResult:
    """Faz uma chamada real ao motor de IA escolhido para validar a chave."""
    try:
        return TesteIAResult(ok=True, mensagem=testar_ia_service(db))
    except HTTPException as e:
        return TesteIAResult(ok=False, mensagem=str(e.detail))


@router.post("/testar-linkedin", response_model=TesteIAResult)
def testar_linkedin(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TesteIAResult:
    """Valida as credenciais do provedor (chama a API real do Unipile)."""
    nome = get_provider_name(db)
    if nome == "mock":
        return TesteIAResult(ok=True, mensagem="Provedor simulado (mock) — sempre disponível.")
    try:
        from app.providers.unipile import UnipileProvider

        dsn, key, account_id = get_unipile(db)
        provider = UnipileProvider(dsn=dsn, api_key=key, account_id=account_id)
        return TesteIAResult(ok=True, mensagem=provider.testar())
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
        dsn, key, account_id = get_unipile(db)
        pronto = bool(key and dsn and account_id)
        if pronto:
            aviso = ""
        elif not key or not dsn:
            aviso = _AVISO_UNIPILE_SEM_CHAVE
        else:
            aviso = (
                "Falta o Account ID do Unipile — copie da página Accounts do painel deles."
            )
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
        # valida de verdade contra a API do Unipile antes de marcar como conectado
        from app.providers.unipile import UnipileProvider

        dsn, key, account_id = get_unipile(db)
        if not account_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Preencha o Account ID do Unipile (página Accounts do painel deles) "
                    "antes de conectar."
                ),
            )
        cliente = UnipileProvider(dsn=dsn, api_key=key, account_id=account_id)
        contas = cliente.listar_contas()
        encontrada = next((c for c in contas if str(c.get("id")) == account_id), None)
        if encontrada is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"O Account ID '{account_id}' não foi encontrado nas contas do seu "
                    "Unipile. Confira o ID na página Accounts."
                ),
            )
        external_id = account_id
        token_guardado = key
        nome_conta = dados.nome or str(encontrada.get("name") or "LinkedIn")
    elif provider == "mock":
        external_id = "mock-account-1"
        token_guardado = "token-simulado"
        nome_conta = dados.nome
    else:
        raise HTTPException(status_code=400, detail=f"Provedor desconhecido: {provider}")

    conta = _get_account(db)
    if conta is None:
        conta = LinkedInAccount()
        db.add(conta)

    conta.nome = nome_conta
    conta.provider = provider
    conta.external_account_id = external_id
    conta.status = "CONECTADO"
    conta.token_cifrado = encrypt_token(token_guardado)
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
