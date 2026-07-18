"""Recorrências de post — a Maya publica sozinha no ritmo definido."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.recorrencia import PostRecorrencia
from app.models.user import User
from app.services.recorrencia import processar_recorrencias

router = APIRouter(prefix="/recorrencias", tags=["recorrencias"])


class RecorrenciaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=160)
    tema: str = Field(min_length=1)
    frequencia: str = Field(default="SEMANAL", pattern="^(DIARIO|SEMANAL)$")
    dias_semana: str = ""  # "0,2,4" (0=segunda)
    hora: int = Field(default=9, ge=0, le=23)
    imagem_path: str = ""
    gerar_imagem_ia: bool = False
    publicar_automatico: bool = True
    ativo: bool = True


class RecorrenciaCreate(RecorrenciaBase):
    pass


class RecorrenciaUpdate(BaseModel):
    nome: str | None = None
    tema: str | None = None
    frequencia: str | None = Field(default=None, pattern="^(DIARIO|SEMANAL)$")
    dias_semana: str | None = None
    hora: int | None = Field(default=None, ge=0, le=23)
    imagem_path: str | None = None
    gerar_imagem_ia: bool | None = None
    publicar_automatico: bool | None = None
    ativo: bool | None = None


class RecorrenciaOut(RecorrenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ultimo_criado_em: datetime | None
    criado_em: datetime


@router.get("", response_model=list[RecorrenciaOut])
def listar(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PostRecorrencia]:
    return list(db.scalars(select(PostRecorrencia).order_by(PostRecorrencia.criado_em.desc())))


@router.post("", response_model=RecorrenciaOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: RecorrenciaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PostRecorrencia:
    if dados.frequencia == "SEMANAL" and not dados.dias_semana.strip():
        raise HTTPException(
            status_code=400,
            detail="Escolha pelo menos um dia da semana.",
        )
    r = PostRecorrencia(**dados.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.put("/{rec_id}", response_model=RecorrenciaOut)
def atualizar(
    rec_id: int,
    dados: RecorrenciaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PostRecorrencia:
    r = db.get(PostRecorrencia, rec_id)
    if not r:
        raise HTTPException(status_code=404, detail="Recorrência não encontrada")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(r, campo, valor)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{rec_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    rec_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    r = db.get(PostRecorrencia, rec_id)
    if not r:
        raise HTTPException(status_code=404, detail="Recorrência não encontrada")
    db.delete(r)
    db.commit()


@router.post("/rodar-agora", response_model=dict)
def rodar_agora(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Força a checagem das recorrências (para testar sem esperar a hora)."""
    return processar_recorrencias(db)
