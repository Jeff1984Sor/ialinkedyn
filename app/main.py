"""Ponto de entrada da API do IALinkedyn."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Funcionário virtual de LinkedIn — API (single-tenant).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["infra"])
def health() -> dict:
    """Checagem simples de saúde (usada no deploy/monitoramento)."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "linkedin_provider": settings.linkedin_provider,
    }


# Os routers (auth, knowledge, leads, agents, ...) entram nas próximas etapas.
