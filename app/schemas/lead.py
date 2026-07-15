"""Schemas de Lead."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LeadStatus


class LeadBase(BaseModel):
    nome: str = Field(min_length=1, max_length=180)
    headline: str = ""
    empresa: str = ""
    cargo: str = ""
    linkedin_url: str = ""
    origem: str = ""
    status: LeadStatus = LeadStatus.NOVO
    notas: str = ""


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    nome: str | None = None
    headline: str | None = None
    empresa: str | None = None
    cargo: str | None = None
    linkedin_url: str | None = None
    origem: str | None = None
    status: LeadStatus | None = None
    notas: str | None = None


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
