"""Serviço de campanha: enfileirar e enviar abordagens em ritmo humano.

Anti-ban: respeita limites diários, horário de trabalho e envia uma de cada vez
(o worker chama `processar_fila` periodicamente).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.connection import AutomationSettings
from app.models.conversation import Conversation, Message
from app.models.enums import LeadStatus, MessageAuthor
from app.models.lead import Lead
from app.models.outreach import OutreachStatus, OutreachTask, OutreachTipo
from app.providers.factory import get_provider

# BRT (o servidor roda em UTC)
FUSO_BR = timezone(timedelta(hours=-3))


def get_settings(db: Session) -> AutomationSettings:
    cfg = db.scalar(select(AutomationSettings).limit(1))
    if cfg is None:
        cfg = AutomationSettings()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _inicio_do_dia_utc() -> datetime:
    agora_br = datetime.now(FUSO_BR)
    inicio_br = agora_br.replace(hour=0, minute=0, second=0, microsecond=0)
    return inicio_br.astimezone(timezone.utc)


def enviados_hoje(db: Session) -> int:
    return (
        db.scalar(
            select(func.count(OutreachTask.id)).where(
                OutreachTask.status == OutreachStatus.ENVIADO,
                OutreachTask.enviado_em >= _inicio_do_dia_utc(),
            )
        )
        or 0
    )


def dentro_do_horario(cfg: AutomationSettings) -> bool:
    hora = datetime.now(FUSO_BR).hour
    if cfg.horario_inicio <= cfg.horario_fim:
        return cfg.horario_inicio <= hora < cfg.horario_fim
    # janela que cruza a meia-noite
    return hora >= cfg.horario_inicio or hora < cfg.horario_fim


def limite_diario(cfg: AutomationSettings) -> int:
    """Usa o menor entre convites e mensagens — o gargalo manda."""
    return min(cfg.limite_convites_dia, cfg.limite_mensagens_dia)


def restante_hoje(db: Session) -> int:
    cfg = get_settings(db)
    return max(0, limite_diario(cfg) - enviados_hoje(db))


def enfileirar(
    db: Session,
    lead_id: int,
    mensagem: str,
    tipo: str = OutreachTipo.CONVITE,
    audience_id: int | None = None,
) -> OutreachTask:
    tarefa = OutreachTask(
        lead_id=lead_id,
        audience_id=audience_id,
        tipo=tipo,
        mensagem=mensagem,
        status=OutreachStatus.PENDENTE,
    )
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    return tarefa


def _registrar_conversa(db: Session, lead: Lead, texto: str) -> None:
    """Guarda a mensagem enviada no nosso CRM (histórico da conversa)."""
    conversa = db.scalar(select(Conversation).where(Conversation.lead_id == lead.id))
    if conversa is None:
        conversa = Conversation(lead_id=lead.id, canal="linkedin")
        db.add(conversa)
        db.flush()
    db.add(
        Message(
            conversation_id=conversa.id,
            autor=MessageAuthor.EU.value,
            conteudo=texto,
        )
    )


def enviar_tarefa(db: Session, tarefa: OutreachTask) -> bool:
    """Envia UMA abordagem. Devolve True se enviou."""
    lead = db.get(Lead, tarefa.lead_id)
    if lead is None:
        tarefa.status = OutreachStatus.CANCELADO
        tarefa.erro = "Lead não existe mais"
        db.commit()
        return False

    if not lead.linkedin_url and not lead.provider_id:
        tarefa.status = OutreachStatus.ERRO
        tarefa.erro = (
            "Lead sem URL do LinkedIn e sem ID do provedor — não dá para identificar "
            "a pessoa. Importe-o pela busca."
        )
        db.commit()
        return False

    provider = get_provider(db)
    try:
        # o id interno pode já estar salvo no lead (vindo da busca)
        pid = (lead.provider_id or "").strip()

        if tarefa.tipo in (OutreachTipo.MENSAGEM, OutreachTipo.FOLLOWUP, OutreachTipo.INMAIL):
            if not pid:
                pid = provider.obter_perfil(lead.linkedin_url).provider_id
                lead.provider_id = pid
            enviar = getattr(provider, "iniciar_conversa", None)
            if enviar is None:
                raise HTTPException(status_code=501, detail="Provedor não suporta iniciar conversa")
            # InMail é o único jeito de falar no chat com quem NÃO é conexão
            enviar(pid, tarefa.mensagem, inmail=(tarefa.tipo == OutreachTipo.INMAIL))
        else:
            # convite com nota (padrão para quem ainda não é conexão)
            provider.enviar_convite(lead.linkedin_url, tarefa.mensagem, provider_id=pid)

        tarefa.status = OutreachStatus.ENVIADO
        tarefa.enviado_em = datetime.now(timezone.utc)
        tarefa.erro = ""

        # reflete no CRM
        _registrar_conversa(db, lead, tarefa.mensagem)
        if tarefa.tipo == OutreachTipo.CONVITE:
            if lead.status in (LeadStatus.NOVO.value, LeadStatus.SEGUINDO.value):
                lead.status = LeadStatus.CONVIDADO.value
        else:
            # mensagem/follow-up/inmail = já falamos com a pessoa
            if lead.status != LeadStatus.RESPONDEU.value:
                lead.status = LeadStatus.ABORDADO.value
        db.commit()
        return True

    except HTTPException as e:
        tarefa.status = OutreachStatus.ERRO
        tarefa.erro = str(e.detail)[:500]
        db.commit()
        return False
    except Exception as e:  # pragma: no cover
        tarefa.status = OutreachStatus.ERRO
        tarefa.erro = str(e)[:500]
        db.commit()
        return False


def processar_fila(db: Session, maximo: int = 1) -> dict:
    """Chamado pelo worker. Envia até `maximo` abordagens, se permitido."""
    cfg = get_settings(db)

    if not dentro_do_horario(cfg):
        return {"enviados": 0, "motivo": "fora do horário de trabalho"}

    disponivel = restante_hoje(db)
    if disponivel <= 0:
        return {"enviados": 0, "motivo": "limite diário atingido"}

    quantidade = min(maximo, disponivel)
    pendentes = list(
        db.scalars(
            select(OutreachTask)
            .where(OutreachTask.status == OutreachStatus.PENDENTE)
            .order_by(OutreachTask.criado_em)
            .limit(quantidade)
        )
    )
    if not pendentes:
        return {"enviados": 0, "motivo": "fila vazia"}

    enviados = sum(1 for t in pendentes if enviar_tarefa(db, t))
    return {"enviados": enviados, "motivo": "ok"}
