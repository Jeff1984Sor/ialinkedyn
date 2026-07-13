"""Model de usuário (login do painel — single-tenant).

Login por **usuário** (username), não por e-mail. Uso interno.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
