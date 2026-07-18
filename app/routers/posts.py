"""Conteúdo — criar posts com IA, agendar e publicar no feed."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import prompt_store
from app.agents.prompts import montar_criador
from app.core.deps import get_current_user, get_db
from app.models.post import Post, PostStatus
from app.models.user import User
from app.services.brand import get_or_create_brand
from app.services.ia import gerar
from app.services.publisher import publicar_post

router = APIRouter(prefix="/posts", tags=["posts"])


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    tema: str
    status: str
    agendado_para: datetime | None
    publicado_em: datetime | None
    external_id: str
    erro: str
    criado_em: datetime


class PostCreate(BaseModel):
    texto: str = Field(min_length=1)
    tema: str = ""
    agendado_para: datetime | None = None


class PostUpdate(BaseModel):
    texto: str | None = None
    tema: str | None = None
    agendado_para: datetime | None = None
    status: str | None = Field(default=None, pattern="^(RASCUNHO|AGENDADO)$")


class GerarRequest(BaseModel):
    tema: str = Field(min_length=1, description="Sobre o que a IA deve escrever")
    salvar: bool = True


class GerarResponse(BaseModel):
    texto: str
    post_id: int | None = None


@router.get("", response_model=list[PostOut])
def listar(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Post]:
    return list(db.scalars(select(Post).order_by(Post.criado_em.desc())))


@router.post("/gerar", response_model=GerarResponse)
def gerar_post(
    dados: GerarRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> GerarResponse:
    """A IA escreve um post no tom da marca sobre o tema pedido."""
    brand = get_or_create_brand(db)
    template = prompt_store.resolver(db, "criador")
    texto = gerar(db, montar_criador(template, brand, dados.tema))

    post_id = None
    if dados.salvar:
        post = Post(texto=texto, tema=dados.tema, status=PostStatus.RASCUNHO)
        db.add(post)
        db.commit()
        db.refresh(post)
        post_id = post.id

    return GerarResponse(texto=texto, post_id=post_id)


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: PostCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Post:
    post = Post(
        texto=dados.texto,
        tema=dados.tema,
        agendado_para=dados.agendado_para,
        status=PostStatus.AGENDADO if dados.agendado_para else PostStatus.RASCUNHO,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/{post_id}", response_model=PostOut)
def atualizar(
    post_id: int,
    dados: PostUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    if post.status == PostStatus.PUBLICADO:
        raise HTTPException(status_code=400, detail="Este post já foi publicado.")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(post, campo, valor)

    # agendou? então marca como agendado
    if dados.agendado_para is not None:
        post.status = PostStatus.AGENDADO if dados.agendado_para else PostStatus.RASCUNHO

    db.commit()
    db.refresh(post)
    return post


@router.post("/{post_id}/publicar", response_model=PostOut)
def publicar_agora(
    post_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Post:
    """Publica imediatamente no feed do LinkedIn."""
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    if post.status == PostStatus.PUBLICADO:
        raise HTTPException(status_code=400, detail="Este post já foi publicado.")

    publicar_post(db, post)
    db.refresh(post)
    if post.status == PostStatus.ERRO:
        raise HTTPException(status_code=502, detail=post.erro or "Falha ao publicar.")
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    post_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    db.delete(post)
    db.commit()
