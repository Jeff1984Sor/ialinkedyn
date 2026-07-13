"""Camada de banco (SQLAlchemy 2.0).

Expõe: engine, SessionLocal, Base e o dependency get_db.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # evita conexões mortas (importante em VPS)
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Base declarativa de todos os models."""


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI: abre uma sessão por request e fecha ao fim."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
