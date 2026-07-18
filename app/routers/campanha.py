"""Campanha de prospecção — enfileira abordagens personalizadas e mostra a fila."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents import prompt_store
from app.agents.prompts import montar_cacador
from app.core.deps import get_current_user, get_db
from app.models.audience import Audience
from app.models.lead import Lead
from app.models.outreach import OutreachStatus, OutreachTask
from app.models.user import User
from app.schemas.audience import CampanhaRequest, CampanhaResponse, FilaStatus, TarefaOut
from app.services.brand import get_or_create_brand
from app.services.ia import gerar
from app.services.outreach import (
    dentro_do_horario,
    enfileirar,
    enviados_hoje,
    get_settings,
    limite_diario,
    restante_hoje,
)

router = APIRouter(prefix="/campanha", tags=["campanha"])


@router.post("/enfileirar", response_model=CampanhaResponse)
def enfileirar_campanha(
    dados: CampanhaRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CampanhaResponse:
    """Para cada perfil selecionado: cria/acha o lead, a IA escreve uma mensagem
    personalizada e a abordagem entra na fila (o worker envia em ritmo humano)."""
    if not dados.perfis:
        raise HTTPException(status_code=400, detail="Nenhum perfil selecionado.")

    brand = get_or_create_brand(db)
    template = prompt_store.resolver(db, "cacador")

    contexto_publico = ""
    if dados.audience_id:
        publico = db.get(Audience, dados.audience_id)
        if publico and publico.descricao:
            contexto_publico = f"\nContexto deste público: {publico.descricao}"

    leads_criados = 0
    enfileirados = 0
    ja_abordados = 0

    for p in dados.perfis:
        # 1) lead (sem duplicar)
        lead = None
        if p.linkedin_url:
            lead = db.scalar(select(Lead).where(Lead.linkedin_url == p.linkedin_url))
        if lead is None:
            lead = Lead(
                nome=p.nome or "(sem nome)",
                headline=p.headline,
                empresa=p.empresa,
                cargo=p.cargo,
                linkedin_url=p.linkedin_url,
                origem="Campanha LinkedIn",
                status="NOVO",
                notas=p.sobre,
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            leads_criados += 1

        # 2) não abordar de novo quem já tem tarefa pendente/enviada
        existente = db.scalar(
            select(OutreachTask).where(
                OutreachTask.lead_id == lead.id,
                OutreachTask.status.in_([OutreachStatus.PENDENTE, OutreachStatus.ENVIADO]),
            )
        )
        if existente:
            ja_abordados += 1
            continue

        # 3) a IA escreve a mensagem personalizada deste perfil
        perfil_texto = "\n".join(
            filter(
                None,
                [
                    f"Nome: {p.nome}",
                    f"Headline: {p.headline}" if p.headline else "",
                    f"Empresa: {p.empresa}" if p.empresa else "",
                    f"Cargo: {p.cargo}" if p.cargo else "",
                    f"Sobre: {p.sobre}" if p.sobre else "",
                    ("Posts recentes: " + " | ".join(p.posts_recentes)) if p.posts_recentes else "",
                    contexto_publico,
                ],
            )
        )
        mensagem = gerar(db, montar_cacador(template, brand, perfil_texto))

        # convite do LinkedIn tem limite de 300 caracteres
        if dados.tipo == "CONVITE" and len(mensagem) > 300:
            mensagem = mensagem[:297].rstrip() + "..."

        enfileirar(db, lead.id, mensagem, tipo=dados.tipo, audience_id=dados.audience_id)
        enfileirados += 1

    cfg = get_settings(db)
    limite = limite_diario(cfg)
    restante = restante_hoje(db)

    aviso = ""
    if enfileirados > restante:
        aviso = (
            f"Você enfileirou {enfileirados} abordagens, mas o limite de hoje permite "
            f"{restante}. O restante será enviado nos próximos dias, automaticamente."
        )
    elif not dentro_do_horario(cfg):
        aviso = (
            f"Fora do horário de trabalho ({cfg.horario_inicio}h-{cfg.horario_fim}h). "
            "O envio começa quando entrar na janela."
        )

    return CampanhaResponse(
        enfileirados=enfileirados,
        leads_criados=leads_criados,
        ja_abordados=ja_abordados,
        limite_diario=limite,
        restante_hoje=restante,
        aviso=aviso,
    )


@router.get("/status", response_model=FilaStatus)
def status_fila(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FilaStatus:
    cfg = get_settings(db)

    pendentes = db.scalar(
        select(func.count(OutreachTask.id)).where(OutreachTask.status == OutreachStatus.PENDENTE)
    ) or 0
    erros = db.scalar(
        select(func.count(OutreachTask.id)).where(OutreachTask.status == OutreachStatus.ERRO)
    ) or 0

    tarefas = list(
        db.scalars(
            select(OutreachTask).order_by(OutreachTask.criado_em.desc()).limit(50)
        )
    )
    saida: list[TarefaOut] = []
    for t in tarefas:
        lead = db.get(Lead, t.lead_id)
        item = TarefaOut.model_validate(t)
        item.lead_nome = lead.nome if lead else ""
        saida.append(item)

    return FilaStatus(
        pendentes=pendentes,
        enviados_hoje=enviados_hoje(db),
        erros=erros,
        limite_diario=limite_diario(cfg),
        restante_hoje=restante_hoje(db),
        dentro_do_horario=dentro_do_horario(cfg),
        horario=f"{cfg.horario_inicio}h - {cfg.horario_fim}h",
        tarefas=saida,
    )


@router.delete("/tarefa/{tarefa_id}", status_code=204)
def cancelar(
    tarefa_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    tarefa = db.get(OutreachTask, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    if tarefa.status == OutreachStatus.ENVIADO:
        raise HTTPException(status_code=400, detail="Essa abordagem já foi enviada.")
    tarefa.status = OutreachStatus.CANCELADO
    db.commit()


@router.post("/enviar-agora", response_model=dict)
def enviar_agora(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Dispara UMA abordagem imediatamente (para testar sem esperar o worker)."""
    from app.services.outreach import processar_fila

    return processar_fila(db, maximo=1)
