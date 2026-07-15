"""Registro central dos models.

Importar tudo aqui garante que o Alembic (e o SQLAlchemy) enxerguem
todas as tabelas via Base.metadata.
"""
from app.core.database import Base
from app.models.brand import BrandVoice
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeItem
from app.models.lead import Lead
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "KnowledgeItem",
    "BrandVoice",
    "Lead",
    "Conversation",
    "Message",
]
