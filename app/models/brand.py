"""Marca / Voz — identidade da funcionária virtual (registro único)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BrandVoice(Base):
    __tablename__ = "brand_voice"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Identidade da funcionária
    nome_assistente: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    persona: Mapped[str] = mapped_column(Text, default="", nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    assina_mensagens: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Voz da empresa
    descricao_empresa: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tom: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icp: Mapped[str] = mapped_column(Text, default="", nullable=False)  # público ideal
    cta: Mapped[str] = mapped_column(Text, default="", nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
