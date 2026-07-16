"""Prompts dos agentes — editáveis pelo painel.

Só guarda o que foi CUSTOMIZADO. Se não houver registro para a chave,
vale o padrão definido em app/agents/prompts.py (DEFAULTS).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_template"

    id: Mapped[int] = mapped_column(primary_key=True)
    chave: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
