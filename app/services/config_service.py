"""Configuração efetiva da ferramenta.

Regra: o que está salvo no PAINEL (banco) manda. O .env serve apenas como
reserva/compatibilidade. Assim o usuário configura tudo pela interface.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decrypt_token, encrypt_token
from app.models.config import AppConfig


def get_config(db: Session) -> AppConfig:
    cfg = db.scalar(select(AppConfig).limit(1))
    if cfg is None:
        cfg = AppConfig(
            linkedin_provider=settings.linkedin_provider or "mock",
            unipile_dsn=settings.unipile_dsn or "",
            gemini_model=settings.gemini_model or "gemini-2.5-flash",
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _decifra(valor: str) -> str:
    if not valor:
        return ""
    try:
        return decrypt_token(valor)
    except Exception:
        # chave Fernet trocada ou dado corrompido -> trata como não configurado
        return ""


def cifra(valor: str) -> str:
    return encrypt_token(valor) if valor else ""


# ------------------------------------------------------------------ IA


def get_ia(db: Session) -> tuple[str, str, str]:
    """Devolve (provider, api_key, model) do motor de IA escolhido."""
    cfg = get_config(db)
    provider = (cfg.ia_provider or "gemini").lower()
    if provider == "openai":
        return "openai", _decifra(cfg.openai_api_key_cifrado), cfg.openai_model or "gpt-4o"
    key = _decifra(cfg.gemini_api_key_cifrado) or settings.gemini_api_key or ""
    return "gemini", key, cfg.gemini_model or settings.gemini_model or "gemini-2.5-flash"


def get_gemini(db: Session) -> tuple[str, str]:
    """(compatibilidade) chave e modelo do Gemini."""
    cfg = get_config(db)
    key = _decifra(cfg.gemini_api_key_cifrado) or settings.gemini_api_key or ""
    return key, cfg.gemini_model or settings.gemini_model or "gemini-2.5-flash"


def get_openai(db: Session) -> tuple[str, str]:
    cfg = get_config(db)
    return _decifra(cfg.openai_api_key_cifrado), cfg.openai_model or "gpt-4o"


# ------------------------------------------------------------------ LinkedIn


def get_provider_name(db: Session) -> str:
    cfg = get_config(db)
    return cfg.linkedin_provider or settings.linkedin_provider or "mock"


def get_unipile(db: Session) -> tuple[str, str, str]:
    """Devolve (dsn, api_key, account_id) efetivos."""
    cfg = get_config(db)
    dsn = cfg.unipile_dsn or settings.unipile_dsn or ""
    key = _decifra(cfg.unipile_api_key_cifrado) or settings.unipile_api_key or ""
    return dsn, key, cfg.unipile_account_id or ""


def mascarar(valor: str) -> str:
    """Mostra só o final da chave (nunca devolve o segredo inteiro)."""
    if not valor:
        return ""
    if len(valor) <= 4:
        return "•" * len(valor)
    return "•" * 8 + valor[-4:]
