"""Conversas e mensagens."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.conversation import Conversation, Message
from app.models.lead import Lead
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetalhe,
    ConversationResumo,
    MessageCreate,
    MessageOut,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResumo])
def listar(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ConversationResumo]:
    conversas = list(db.scalars(select(Conversation).order_by(Conversation.criado_em.desc())))
    resumos: list[ConversationResumo] = []
    for c in conversas:
        lead = db.get(Lead, c.lead_id)
        ultima = c.mensagens[-1] if c.mensagens else None
        resumos.append(
            ConversationResumo(
                id=c.id,
                lead_id=c.lead_id,
                canal=c.canal,
                criado_em=c.criado_em,
                lead_nome=lead.nome if lead else "",
                ultima_mensagem=(ultima.conteudo[:120] if ultima else ""),
                ultima_em=ultima.criado_em if ultima else None,
            )
        )
    return resumos


@router.post("", response_model=ConversationDetalhe, status_code=status.HTTP_201_CREATED)
def criar(
    dados: ConversationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConversationDetalhe:
    lead = db.get(Lead, dados.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    conversa = Conversation(lead_id=dados.lead_id, canal=dados.canal)
    db.add(conversa)
    db.commit()
    db.refresh(conversa)
    return _detalhe(db, conversa)


@router.get("/{conversa_id}", response_model=ConversationDetalhe)
def obter(
    conversa_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConversationDetalhe:
    conversa = db.get(Conversation, conversa_id)
    if not conversa:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return _detalhe(db, conversa)


@router.post("/{conversa_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def adicionar_mensagem(
    conversa_id: int,
    dados: MessageCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Message:
    conversa = db.get(Conversation, conversa_id)
    if not conversa:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    msg = Message(
        conversation_id=conversa_id,
        autor=dados.autor.value,
        conteudo=dados.conteudo,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.delete("/{conversa_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    conversa_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    conversa = db.get(Conversation, conversa_id)
    if not conversa:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    db.delete(conversa)
    db.commit()


def _detalhe(db: Session, conversa: Conversation) -> ConversationDetalhe:
    lead = db.get(Lead, conversa.lead_id)
    return ConversationDetalhe(
        id=conversa.id,
        lead_id=conversa.lead_id,
        canal=conversa.canal,
        criado_em=conversa.criado_em,
        lead_nome=lead.nome if lead else "",
        mensagens=[MessageOut.model_validate(m) for m in conversa.mensagens],
    )
