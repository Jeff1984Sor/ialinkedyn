"""Banco de Perguntas & Respostas (o cérebro)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KnowledgeItem(Base):
    __tablename__ = "knowledge_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    pergunta: Mapped[str] = mapped_column(Text, nullable=False)
    resposta: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    categoria: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
