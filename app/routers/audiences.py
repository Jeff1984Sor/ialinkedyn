"""CRUD de Públicos-alvo."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.audience import Audience
from app.models.user import User
from app.schemas.audience import AudienceCreate, AudienceOut, AudienceUpdate

router = APIRouter(prefix="/audiences", tags=["audiences"])


@router.get("", response_model=list[AudienceOut])
def listar(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Audience]:
    return list(db.scalars(select(Audience).order_by(Audience.criado_em.desc())))


@router.post("", response_model=AudienceOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: AudienceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Audience:
    publico = Audience(**dados.model_dump())
    db.add(publico)
    db.commit()
    db.refresh(publico)
    return publico


@router.put("/{publico_id}", response_model=AudienceOut)
def atualizar(
    publico_id: int,
    dados: AudienceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Audience:
    publico = db.get(Audience, publico_id)
    if not publico:
        raise HTTPException(status_code=404, detail="Público não encontrado")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(publico, campo, valor)
    db.commit()
    db.refresh(publico)
    return publico


@router.delete("/{publico_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    publico_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    publico = db.get(Audience, publico_id)
    if not publico:
        raise HTTPException(status_code=404, detail="Público não encontrado")
    db.delete(publico)
    db.commit()
