"""Fila de abordagens — o worker envia aos poucos (ritmo humano, anti-ban)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OutreachStatus:
    PENDENTE = "PENDENTE"
    ENVIADO = "ENVIADO"
    ERRO = "ERRO"
    CANCELADO = "CANCELADO"


class OutreachTipo:
    CONVITE = "CONVITE"      # convite de conexão com nota (para quem não é conexão)
    MENSAGEM = "MENSAGEM"    # mensagem direta no chat (para quem já é conexão)


class OutreachTask(Base):
    """Uma abordagem a enviar para um lead."""

    __tablename__ = "outreach_task"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("lead.id", ondelete="CASCADE"), index=True, nullable=False
    )
    audience_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tipo: Mapped[str] = mapped_column(String(20), default=OutreachTipo.CONVITE, nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default=OutreachStatus.PENDENTE, index=True, nullable=False
    )
    erro: Mapped[str] = mapped_column(Text, default="", nullable=False)

    enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
