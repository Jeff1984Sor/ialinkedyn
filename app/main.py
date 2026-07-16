"""Ponto de entrada da API do IALinkedyn."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    agents,
    auth,
    brand,
    connection,
    conversations,
    dashboard,
    knowledge,
    leads,
    prompts,
)

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


app.include_router(auth.router)
app.include_router(knowledge.router)
app.include_router(brand.router)
app.include_router(leads.router)
app.include_router(conversations.router)
app.include_router(agents.router)
app.include_router(dashboard.router)
app.include_router(connection.router)
app.include_router(prompts.router)
