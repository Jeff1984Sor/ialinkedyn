"""Configuração da ferramenta — editável pelo painel (não pelo .env).

Segredos (chaves de API) ficam criptografados com Fernet.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AppConfig(Base):
    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- Conexão LinkedIn ---
    linkedin_provider: Mapped[str] = mapped_column(String(40), default="mock", nullable=False)
    unipile_dsn: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    unipile_api_key_cifrado: Mapped[str] = mapped_column(String(1000), default="", nullable=False)

    # --- IA (Gemini) ---
    gemini_api_key_cifrado: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    gemini_model: Mapped[str] = mapped_column(String(80), default="gemini-2.5-flash", nullable=False)

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
