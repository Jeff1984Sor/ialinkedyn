"""Prompts dos agentes — ver, editar, restaurar padrão e melhorar com IA."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents import prompt_store
from app.agents.prompts import DEFAULTS, LABELS, PLACEHOLDERS, prompt_melhorar
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.prompt import (
    MelhorarRequest,
    MelhorarResponse,
    PromptOut,
    PromptUpdate,
)
from app.services.ia import gerar

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _montar(db: Session, chave: str) -> PromptOut:
    return PromptOut(
        chave=chave,
        label=LABELS.get(chave, chave),
        conteudo=prompt_store.resolver(db, chave),
        padrao=DEFAULTS.get(chave, ""),
        customizado=prompt_store.eh_customizado(db, chave),
        placeholders=PLACEHOLDERS.get(chave, []),
    )


@router.get("", response_model=list[PromptOut])
def listar(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PromptOut]:
    return [_montar(db, chave) for chave in DEFAULTS]


@router.put("/{chave}", response_model=PromptOut)
def atualizar(
    chave: str,
    dados: PromptUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PromptOut:
    if chave not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    prompt_store.salvar(db, chave, dados.conteudo)
    return _montar(db, chave)


@router.delete("/{chave}", response_model=PromptOut)
def restaurar(
    chave: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PromptOut:
    if chave not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    prompt_store.restaurar_padrao(db, chave)
    return _montar(db, chave)


@router.post("/{chave}/melhorar", response_model=MelhorarResponse)
def melhorar(
    chave: str,
    dados: MelhorarRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MelhorarResponse:
    """Conversa com a IA para reescrever o prompt conforme o pedido."""
    if chave not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")

    atual = dados.conteudo_atual or prompt_store.resolver(db, chave)
    sugestao = gerar(db, prompt_melhorar(chave, atual, dados.instrucao))

    # remove cercas de código, se a IA insistir em usar
    limpo = sugestao.strip()
    if limpo.startswith("```"):
        linhas = limpo.split("\n")
        linhas = linhas[1:] if len(linhas) > 1 else linhas
        if linhas and linhas[-1].strip().startswith("```"):
            linhas = linhas[:-1]
        limpo = "\n".join(linhas).strip()

    return MelhorarResponse(sugestao=limpo)
