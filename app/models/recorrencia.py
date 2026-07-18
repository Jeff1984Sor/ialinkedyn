"""Recorrência de posts — a Maya escreve e publica sozinha, no ritmo definido."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Frequencia:
    DIARIO = "DIARIO"
    SEMANAL = "SEMANAL"


class PostRecorrencia(Base):
    __tablename__ = "post_recorrencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    # tema base: a IA escreve um post NOVO a cada disparo
    tema: Mapped[str] = mapped_column(Text, nullable=False)

    frequencia: Mapped[str] = mapped_column(String(20), default=Frequencia.SEMANAL, nullable=False)
    # dias da semana no formato "0,2,4" (0=segunda ... 6=domingo)
    dias_semana: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    hora: Mapped[int] = mapped_column(Integer, default=9, nullable=False)  # hora BRT

    # imagem fixa opcional para todos os posts desta recorrência
    imagem_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    # ou deixar a IA criar uma imagem nova a cada post
    gerar_imagem_ia: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # publicar direto ou deixar como rascunho para você revisar
    publicar_automatico: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultimo_criado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
