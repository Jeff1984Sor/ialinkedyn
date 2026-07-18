"""Geração de imagem por IA (Gemini ou OpenAI) para ilustrar os posts."""
from __future__ import annotations

import base64
import secrets
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.config_service import get_ia

PASTA = Path("uploads")
PASTA.mkdir(exist_ok=True)

MODELO_GEMINI = "imagen-4.0-generate-001"
MODELO_OPENAI = "gpt-image-1"


def _salvar(conteudo: bytes, ext: str = ".png") -> str:
    nome = f"ia_{secrets.token_hex(8)}{ext}"
    destino = PASTA / nome
    destino.write_bytes(conteudo)
    return str(destino)


def _gerar_gemini(prompt: str, api_key: str) -> str:
    try:
        from google import genai
    except ImportError as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"google-genai não instalado: {e}")

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_images(
            model=MODELO_GEMINI,
            prompt=prompt,
            config={"number_of_images": 1},
        )
        imagens = getattr(resp, "generated_images", None) or []
        if not imagens:
            raise HTTPException(status_code=502, detail="O Gemini não devolveu imagem.")
        bruto = imagens[0].image.image_bytes
        return _salvar(bruto)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(
            status_code=502,
            detail=(
                f"Erro ao gerar imagem no Gemini: {e}. "
                "A geração de imagem costuma exigir chave em plano pago."
            ),
        )


def _gerar_openai(prompt: str, api_key: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"openai não instalado: {e}")

    try:
        client = OpenAI(api_key=api_key)
        resp = client.images.generate(
            model=MODELO_OPENAI,
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        b64 = resp.data[0].b64_json
        if not b64:
            raise HTTPException(status_code=502, detail="A OpenAI não devolveu imagem.")
        return _salvar(base64.b64decode(b64))
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(
            status_code=502,
            detail=(
                f"Erro ao gerar imagem na OpenAI: {e}. "
                "O modelo gpt-image-1 pode exigir verificação da organização."
            ),
        )


def gerar_imagem(db: Session, prompt: str) -> str:
    """Gera a imagem com o motor configurado e devolve o caminho salvo."""
    provider, api_key, _modelo = get_ia(db)
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Configure a chave de IA em Conexões para gerar imagens.",
        )
    if provider == "openai":
        return _gerar_openai(prompt, api_key)
    return _gerar_gemini(prompt, api_key)
