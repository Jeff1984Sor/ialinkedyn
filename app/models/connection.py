"""Conexão com o LinkedIn + configurações de automação (anti-ban)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LinkedInAccount(Base):
    """Conta do LinkedIn vinculada ao painel (via provedor)."""

    __tablename__ = "linkedin_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="mock", nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    # DESCONECTADO | CONECTADO | ERRO
    status: Mapped[str] = mapped_column(String(20), default="DESCONECTADO", nullable=False)
    # token do provedor, criptografado com Fernet (nunca em texto puro)
    token_cifrado: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    conectado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AutomationSettings(Base):
    """Limites diários e ritmo (registro único) — proteção contra ban."""

    __tablename__ = "automation_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    limite_follows_dia: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    limite_convites_dia: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    limite_mensagens_dia: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    # MANUAL = aprovar-e-enviar | AUTO = IA responde sozinha
    modo_chat: Mapped[str] = mapped_column(String(10), default="MANUAL", nullable=False)
    # seguir sozinho todo mundo que aparecer na busca
    seguir_automatico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    horario_inicio: Mapped[int] = mapped_column(Integer, default=9, nullable=False)   # hora (0-23)
    horario_fim: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
