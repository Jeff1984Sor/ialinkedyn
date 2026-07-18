"""Lead (CRM de prospecção)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import LeadStatus


class Lead(Base):
    __tablename__ = "lead"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    headline: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    empresa: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    cargo: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    linkedin_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    # id interno da pessoa no provedor — necessário para convite/mensagem
    provider_id: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    origem: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default=LeadStatus.NOVO.value, nullable=False
    )
    notas: Mapped[str] = mapped_column(Text, default="", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
