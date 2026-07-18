"""Interface da camada de conexão LinkedIn (plugável).

O resto do sistema fala SÓ com esta interface — não sabe se por baixo
está o Mock (desenvolvimento) ou o Unipile (real). Trocar de provedor
= trocar só esta camada (config LINKEDIN_PROVIDER no .env).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PerfilLinkedIn:
    nome: str = ""
    headline: str = ""
    empresa: str = ""
    cargo: str = ""
    linkedin_url: str = ""
    sobre: str = ""
    posts_recentes: list[str] = field(default_factory=list)
    # id interno da pessoa no provedor (necessário para convite/mensagem)
    provider_id: str = ""


@dataclass
class ConversaExterna:
    external_id: str
    nome_lead: str
    ultima_mensagem: str


class LinkedInProvider(ABC):
    """Contrato mínimo que todo provedor de LinkedIn deve implementar."""

    nome: str = "base"

    @abstractmethod
    def buscar_pessoas(self, termo: str, limite: int = 10) -> list[PerfilLinkedIn]:
        ...

    @abstractmethod
    def obter_perfil(self, linkedin_url: str) -> PerfilLinkedIn:
        ...

    @abstractmethod
    def seguir(self, linkedin_url: str) -> bool:
        ...

    @abstractmethod
    def enviar_convite(self, linkedin_url: str, mensagem: str) -> bool:
        ...

    @abstractmethod
    def enviar_mensagem(self, external_id: str, texto: str) -> bool:
        ...

    @abstractmethod
    def publicar_post(self, texto: str) -> str:
        """Publica um post e devolve o identificador/URN."""
        ...
