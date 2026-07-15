"""Estatísticas do dashboard (dados reais)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.conversation import Conversation
from app.models.enums import LeadStatus
from app.models.knowledge import KnowledgeItem
from app.models.lead import Lead
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    total_leads: int
    total_conversas: int
    total_qa: int
    leads_por_status: dict[str, int]


@router.get("/stats", response_model=DashboardStats)
def stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DashboardStats:
    total_leads = db.scalar(select(func.count(Lead.id))) or 0
    total_conversas = db.scalar(select(func.count(Conversation.id))) or 0
    total_qa = db.scalar(select(func.count(KnowledgeItem.id))) or 0

    por_status: dict[str, int] = {s.value: 0 for s in LeadStatus}
    linhas = db.execute(select(Lead.status, func.count(Lead.id)).group_by(Lead.status)).all()
    for st, qtd in linhas:
        por_status[st] = qtd

    return DashboardStats(
        total_leads=total_leads,
        total_conversas=total_conversas,
        total_qa=total_qa,
        leads_por_status=por_status,
    )
