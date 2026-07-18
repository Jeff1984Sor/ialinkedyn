"""Posts do feed — criados pela IA, agendados e publicados pelo worker."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PostStatus:
    RASCUNHO = "RASCUNHO"
    AGENDADO = "AGENDADO"
    PUBLICADO = "PUBLICADO"
    ERRO = "ERRO"


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    tema: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=PostStatus.RASCUNHO, index=True, nullable=False
    )
    agendado_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publicado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imagem_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    erro: Mapped[str] = mapped_column(Text, default="", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
