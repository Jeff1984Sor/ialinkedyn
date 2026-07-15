"""Conversas e mensagens (histórico nunca sobrescrito)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("lead.id", ondelete="CASCADE"), index=True, nullable=False
    )
    canal: Mapped[str] = mapped_column(String(60), default="linkedin", nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    mensagens: Mapped[list["Message"]] = relationship(
        back_populates="conversa",
        cascade="all, delete-orphan",
        order_by="Message.criado_em",
    )


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), index=True, nullable=False
    )
    autor: Mapped[str] = mapped_column(String(20), nullable=False)  # LEAD | EU | IA_RASCUNHO
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversa: Mapped["Conversation"] = relationship(back_populates="mensagens")
