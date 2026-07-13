"""Registro central dos models.

Importar tudo aqui garante que o Alembic (e o SQLAlchemy) enxerguem
todas as tabelas via Base.metadata.
"""
from app.core.database import Base
from app.models.user import User

__all__ = ["Base", "User"]
