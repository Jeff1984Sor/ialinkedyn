"""Público-alvo salvo — usado pelo Caçador para buscar no LinkedIn."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Audience(Base):
    __tablename__ = "audience"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    # termo/palavras-chave que vão para a busca do LinkedIn
    termo: Mapped[str] = mapped_column(Text, nullable=False)
    # contexto extra que ajuda a IA a personalizar a abordagem deste público
    descricao: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
