"""Wrapper do Google Gemini (google-genai).

A chave e o modelo vêm da configuração do PAINEL (banco). Se não houver
chave configurada, levanta erro claro para a UI avisar o usuário.
"""
from __future__ import annotations

from fastapi import HTTPException


def gerar_texto(prompt: str, api_key: str, model: str) -> str:
    """Gera texto com o Gemini a partir de um prompt único."""
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Chave do Gemini não configurada. Vá em Conexões → Inteligência "
                "Artificial e cole sua GEMINI API KEY."
            ),
        )
    try:
        from google import genai
    except ImportError as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"google-genai não instalado: {e}")

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model, contents=prompt)
        return (resp.text or "").strip()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Erro ao chamar o Gemini: {e}")


def testar_chave(api_key: str, model: str) -> str:
    """Faz uma chamada mínima para validar a chave. Devolve a resposta."""
    return gerar_texto("Responda apenas: OK", api_key, model)
