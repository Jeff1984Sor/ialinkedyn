"""Recorrências — cria (e publica) posts automaticamente no ritmo definido."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import prompt_store
from app.agents.prompts import montar_criador, montar_designer
from app.models.post import Post, PostStatus
from app.models.recorrencia import Frequencia, PostRecorrencia
from app.services.brand import get_or_create_brand
from app.services.ia import gerar
from app.services.image_gen import gerar_imagem
from app.services.publisher import publicar_post

log = logging.getLogger("ialinkedyn.recorrencia")

FUSO_BR = timezone(timedelta(hours=-3))


def _deve_disparar(r: PostRecorrencia, agora_br: datetime) -> bool:
    if not r.ativo:
        return False
    if agora_br.hour != r.hora:
        return False

    if r.frequencia == Frequencia.SEMANAL:
        dias = [d.strip() for d in (r.dias_semana or "").split(",") if d.strip()]
        if str(agora_br.weekday()) not in dias:
            return False

    # já criou hoje?
    if r.ultimo_criado_em:
        ultimo_br = r.ultimo_criado_em.astimezone(FUSO_BR)
        if ultimo_br.date() == agora_br.date():
            return False

    return True


def processar_recorrencias(db: Session) -> dict:
    """Chamado pelo worker: cria os posts das recorrências que venceram."""
    agora_br = datetime.now(FUSO_BR)
    recorrencias = list(db.scalars(select(PostRecorrencia).where(PostRecorrencia.ativo.is_(True))))
    if not recorrencias:
        return {"criados": 0, "publicados": 0, "motivo": "nenhuma recorrência ativa"}

    brand = get_or_create_brand(db)
    template = prompt_store.resolver(db, "criador")

    criados = publicados = 0
    for r in recorrencias:
        if not _deve_disparar(r, agora_br):
            continue

        try:
            texto = gerar(db, montar_criador(template, brand, r.tema))
        except Exception:  # pragma: no cover
            log.exception("Falha ao gerar post da recorrência %s", r.id)
            continue

        imagem = r.imagem_path
        if r.gerar_imagem_ia:
            try:
                template_img = prompt_store.resolver(db, "designer")
                prompt_img = gerar(db, montar_designer(template_img, brand, r.tema))
                imagem = gerar_imagem(db, prompt_img)
            except Exception:  # imagem é opcional: post sai mesmo sem ela
                log.exception("Falha ao gerar imagem da recorrência %s", r.id)
                imagem = r.imagem_path

        post = Post(
            texto=texto,
            tema=f"[{r.nome}] {r.tema}"[:300],
            imagem_path=imagem,
            status=PostStatus.RASCUNHO,
        )
        db.add(post)
        r.ultimo_criado_em = datetime.now(timezone.utc)
        db.commit()
        db.refresh(post)
        criados += 1

        if r.publicar_automatico:
            if publicar_post(db, post):
                publicados += 1

    return {"criados": criados, "publicados": publicados, "motivo": "ok"}
