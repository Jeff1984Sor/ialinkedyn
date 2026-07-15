"""Marca / Voz — registro único de configuração."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.brand import BrandVoiceOut, BrandVoiceUpdate
from app.services.brand import get_or_create_brand

router = APIRouter(prefix="/brand", tags=["brand"])


@router.get("", response_model=BrandVoiceOut)
def obter(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_or_create_brand(db)


@router.put("", response_model=BrandVoiceOut)
def atualizar(
    dados: BrandVoiceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    brand = get_or_create_brand(db)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(brand, campo, valor)
    db.commit()
    db.refresh(brand)
    return brand
