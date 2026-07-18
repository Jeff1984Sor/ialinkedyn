"""Motor de crescimento da rede.

- Detecta quem ACEITOU o convite (comparando com suas conexões no LinkedIn)
- Ao detectar, enfileira automaticamente a 1ª mensagem no chat (follow-up)
- Sincroniza suas conexões para virarem leads no CRM
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import prompt_store
from app.agents.prompts import montar_cacador
from app.models.enums import LeadStatus
from app.models.lead import Lead
from app.models.outreach import OutreachStatus, OutreachTask, OutreachTipo
from app.providers.factory import get_provider
from app.services.brand import get_or_create_brand
from app.services.ia import gerar
from app.services.outreach import enfileirar

log = logging.getLogger("ialinkedyn.growth")


def _perfil_texto(lead: Lead) -> str:
    return "\n".join(
        filter(
            None,
            [
                f"Nome: {lead.nome}",
                f"Headline: {lead.headline}" if lead.headline else "",
                f"Empresa: {lead.empresa}" if lead.empresa else "",
                f"Cargo: {lead.cargo}" if lead.cargo else "",
                f"Notas: {lead.notas}" if lead.notas else "",
            ],
        )
    )


def _ids_das_conexoes(db: Session, paginas: int = 5) -> set[str]:
    """Busca suas conexões no LinkedIn (paginado) e devolve os provider_ids."""
    provider = get_provider(db)
    listar = getattr(provider, "listar_relacoes", None)
    if listar is None:
        return set()

    ids: set[str] = set()
    cursor = ""
    for _ in range(paginas):
        perfis, cursor = listar(limite=100, cursor=cursor)
        for p in perfis:
            if p.provider_id:
                ids.add(p.provider_id)
        if not cursor:
            break
    return ids


def detectar_aceites(db: Session) -> dict:
    """Quem foi convidado e agora está na sua lista de conexões = aceitou.

    Para cada aceite: muda o status do lead e enfileira o follow-up.
    """
    convidados = list(
        db.scalars(
            select(Lead).where(
                Lead.status == LeadStatus.CONVIDADO.value,
                Lead.provider_id != "",
            )
        )
    )
    if not convidados:
        return {"aceites": 0, "followups": 0, "motivo": "ninguém aguardando aceite"}

    conexoes = _ids_das_conexoes(db)
    if not conexoes:
        return {"aceites": 0, "followups": 0, "motivo": "não consegui listar conexões"}

    brand = get_or_create_brand(db)
    template = prompt_store.resolver(db, "followup")

    aceites = followups = 0
    for lead in convidados:
        if lead.provider_id not in conexoes:
            continue

        lead.status = LeadStatus.CONECTADO.value
        aceites += 1

        # já existe follow-up para este lead?
        existente = db.scalar(
            select(OutreachTask).where(
                OutreachTask.lead_id == lead.id,
                OutreachTask.tipo == OutreachTipo.FOLLOWUP,
                OutreachTask.status.in_([OutreachStatus.PENDENTE, OutreachStatus.ENVIADO]),
            )
        )
        if existente:
            continue

        try:
            mensagem = gerar(db, montar_cacador(template, brand, _perfil_texto(lead)))
        except Exception:  # pragma: no cover
            log.exception("Falha ao gerar follow-up do lead %s", lead.id)
            continue

        enfileirar(db, lead.id, mensagem, tipo=OutreachTipo.FOLLOWUP)
        followups += 1

    db.commit()
    return {"aceites": aceites, "followups": followups, "motivo": "ok"}


def sincronizar_conexoes(db: Session, paginas: int = 5) -> dict:
    """Traz suas conexões do LinkedIn para o CRM (sem duplicar)."""
    provider = get_provider(db)
    listar = getattr(provider, "listar_relacoes", None)
    if listar is None:
        return {"importados": 0, "motivo": "provedor não suporta listar conexões"}

    existentes = {
        pid
        for (pid,) in db.execute(select(Lead.provider_id).where(Lead.provider_id != "")).all()
    }

    importados = 0
    cursor = ""
    for _ in range(paginas):
        perfis, cursor = listar(limite=100, cursor=cursor)
        for p in perfis:
            if not p.provider_id or p.provider_id in existentes:
                continue
            db.add(
                Lead(
                    nome=p.nome or "(sem nome)",
                    headline=p.headline,
                    linkedin_url=p.linkedin_url,
                    provider_id=p.provider_id,
                    origem="Minhas conexões",
                    status=LeadStatus.CONECTADO.value,
                )
            )
            existentes.add(p.provider_id)
            importados += 1
        if not cursor:
            break

    db.commit()
    return {"importados": importados, "motivo": "ok"}
