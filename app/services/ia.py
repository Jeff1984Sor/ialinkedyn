"""Camada de IA unificada — Google Gemini OU OpenAI.

O resto do sistema chama `gerar(db, prompt)` e não precisa saber qual motor
está configurado no painel.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.config_service import get_ia


@dataclass
class MotorIA:
    provider: str  # gemini | openai
    api_key: str
    model: str


def _gerar_gemini(prompt: str, api_key: str, model: str) -> str:
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


def _gerar_openai(prompt: str, api_key: str, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"openai não instalado: {e}")
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Erro ao chamar a OpenAI: {e}")


def gerar_com(motor: MotorIA, prompt: str) -> str:
    if not motor.api_key:
        nome = "Gemini" if motor.provider == "gemini" else "OpenAI"
        raise HTTPException(
            status_code=503,
            detail=(
                f"Chave da {nome} não configurada. Vá em Conexões → Inteligência "
                f"Artificial e cole sua chave."
            ),
        )
    if motor.provider == "openai":
        return _gerar_openai(prompt, motor.api_key, motor.model)
    return _gerar_gemini(prompt, motor.api_key, motor.model)


def gerar(db: Session, prompt: str) -> str:
    """Gera texto usando o motor configurado no painel."""
    provider, api_key, model = get_ia(db)
    return gerar_com(MotorIA(provider, api_key, model), prompt)


def testar(db: Session) -> str:
    """Chamada mínima para validar a chave configurada."""
    provider, api_key, model = get_ia(db)
    resposta = gerar_com(MotorIA(provider, api_key, model), "Responda apenas: OK")
    nome = "OpenAI" if provider == "openai" else "Gemini"
    return f"{nome} funcionando! ({model}) → {resposta[:60]}"
