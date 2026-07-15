"""CRUD do Banco de Perguntas & Respostas."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.schemas.knowledge import KnowledgeCreate, KnowledgeOut, KnowledgeUpdate

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeOut])
def listar(
    q: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[KnowledgeItem]:
    stmt = select(KnowledgeItem).order_by(KnowledgeItem.criado_em.desc())
    itens = list(db.scalars(stmt))
    if q:
        termo = q.lower()
        itens = [
            k for k in itens
            if termo in k.pergunta.lower()
            or termo in k.resposta.lower()
            or termo in k.tags.lower()
            or termo in k.categoria.lower()
        ]
    return itens


@router.post("", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: KnowledgeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeItem:
    item = KnowledgeItem(**dados.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=KnowledgeOut)
def atualizar(
    item_id: int,
    dados: KnowledgeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeItem:
    item = db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    item = db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    db.delete(item)
    db.commit()
