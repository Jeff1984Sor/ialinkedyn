"""CRUD de Leads (CRM)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.lead import Lead
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadOut, LeadUpdate

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadOut])
def listar(
    status_filtro: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Lead]:
    stmt = select(Lead).order_by(Lead.criado_em.desc())
    if status_filtro:
        stmt = stmt.where(Lead.status == status_filtro)
    return list(db.scalars(stmt))


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: LeadCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Lead:
    payload = dados.model_dump()
    payload["status"] = payload["status"].value if hasattr(payload["status"], "value") else payload["status"]
    lead = Lead(**payload)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/{lead_id}", response_model=LeadOut)
def obter(
    lead_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@router.put("/{lead_id}", response_model=LeadOut)
def atualizar(
    lead_id: int,
    dados: LeadUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if campo == "status" and hasattr(valor, "value"):
            valor = valor.value
        setattr(lead, campo, valor)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    lead_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    db.delete(lead)
    db.commit()
