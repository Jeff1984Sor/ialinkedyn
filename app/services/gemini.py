"""Wrapper do Google Gemini (google-genai).

Isola a chamada ao LLM. Se a GEMINI_API_KEY não estiver configurada,
levanta um erro claro (para a UI avisar o usuário).
"""
from __future__ import annotations

from fastapi import HTTPException

from app.core.config import settings

_client = None


def _get_client():
    global _client
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY não configurada no .env do servidor.",
        )
    if _client is None:
        try:
            from google import genai
        except ImportError as e:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"google-genai não instalado: {e}")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def gerar_texto(prompt: str) -> str:
    """Gera texto com o Gemini a partir de um prompt único."""
    client = _get_client()
    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        return (resp.text or "").strip()
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Erro ao chamar o Gemini: {e}")
