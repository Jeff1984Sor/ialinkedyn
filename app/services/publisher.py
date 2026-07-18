"""Publicação de posts no feed do LinkedIn."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import Post, PostStatus
from app.providers.factory import get_provider

log = logging.getLogger("ialinkedyn.publisher")


def publicar_post(db: Session, post: Post) -> bool:
    """Publica UM post. Marca status e guarda o id externo (ou o erro)."""
    try:
        provider = get_provider(db)
        externo = provider.publicar_post(post.texto, imagem_path=post.imagem_path or "")
        post.external_id = str(externo or "")
        post.status = PostStatus.PUBLICADO
        post.publicado_em = datetime.now(timezone.utc)
        post.erro = ""
        db.commit()
        return True
    except HTTPException as e:
        post.status = PostStatus.ERRO
        post.erro = str(e.detail)[:500]
        db.commit()
        return False
    except Exception as e:  # pragma: no cover
        post.status = PostStatus.ERRO
        post.erro = str(e)[:500]
        db.commit()
        return False


def publicar_agendados(db: Session) -> dict:
    """Publica os posts cujo horário agendado já chegou."""
    agora = datetime.now(timezone.utc)
    vencidos = list(
        db.scalars(
            select(Post)
            .where(
                Post.status == PostStatus.AGENDADO,
                Post.agendado_para.is_not(None),
                Post.agendado_para <= agora,
            )
            .order_by(Post.agendado_para)
        )
    )
    if not vencidos:
        return {"publicados": 0, "motivo": "nada agendado para agora"}

    publicados = sum(1 for p in vencidos if publicar_post(db, p))
    return {"publicados": publicados, "motivo": "ok"}
