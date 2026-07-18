"""Registro central dos models.

Importar tudo aqui garante que o Alembic (e o SQLAlchemy) enxerguem
todas as tabelas via Base.metadata.
"""
from app.core.database import Base
from app.models.audience import Audience
from app.models.brand import BrandVoice
from app.models.config import AppConfig
from app.models.connection import AutomationSettings, LinkedInAccount
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeItem
from app.models.lead import Lead
from app.models.outreach import OutreachTask
from app.models.post import Post
from app.models.prompt import PromptTemplate
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "KnowledgeItem",
    "BrandVoice",
    "Lead",
    "Conversation",
    "Message",
    "LinkedInAccount",
    "AutomationSettings",
    "AppConfig",
    "PromptTemplate",
    "Audience",
    "OutreachTask",
    "Post",
]
