"""Upload de imagens para os posts."""
from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/midia", tags=["midia"])

PASTA = Path("uploads")
PASTA.mkdir(exist_ok=True)

EXTENSOES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
TAMANHO_MAX = 10 * 1024 * 1024  # 10 MB


class UploadOut(BaseModel):
    nome: str
    caminho: str
    url: str


@router.post("/upload", response_model=UploadOut)
async def upload(
    arquivo: UploadFile = File(...),
    _: User = Depends(get_current_user),
) -> UploadOut:
    """Envia uma imagem para usar em posts."""
    ext = Path(arquivo.filename or "").suffix.lower()
    if ext not in EXTENSOES:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não aceito. Use: {', '.join(sorted(EXTENSOES))}",
        )

    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAX:
        raise HTTPException(status_code=400, detail="Imagem acima de 10 MB.")

    nome = f"{secrets.token_hex(8)}{ext}"
    destino = PASTA / nome
    destino.write_bytes(conteudo)

    return UploadOut(nome=nome, caminho=str(destino), url=f"/api/midia/{nome}")


@router.get("/{nome}")
def servir(nome: str) -> FileResponse:
    """Serve a imagem enviada (para pré-visualização no painel)."""
    caminho = PASTA / Path(nome).name  # evita path traversal
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    return FileResponse(caminho)
