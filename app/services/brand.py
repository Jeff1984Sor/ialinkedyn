"""Helper para obter (ou criar) o registro único de Marca/Voz."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import BrandVoice


def get_or_create_brand(db: Session) -> BrandVoice:
    brand = db.scalar(select(BrandVoice).limit(1))
    if brand is None:
        brand = BrandVoice()
        db.add(brand)
        db.commit()
        db.refresh(brand)
    return brand
