"""MockProvider — simula o LinkedIn para desenvolver o cérebro sem contratar
um provedor real. Não faz nenhuma chamada externa.
"""
from __future__ import annotations

from app.providers.base import LinkedInProvider, PerfilLinkedIn

_PERFIS_FAKE = [
    PerfilLinkedIn(
        nome="Ana Souza",
        headline="Diretora Comercial na TechCorp",
        empresa="TechCorp",
        cargo="Diretora Comercial",
        linkedin_url="https://linkedin.com/in/ana-souza",
        provider_id="mock-ana",
        sobre="Lidero times de vendas B2B há 12 anos, focada em SaaS.",
        posts_recentes=["Falando sobre previsibilidade de receita no B2B."],
    ),
    PerfilLinkedIn(
        nome="Bruno Lima",
        headline="Fundador na Clínica Bem Viver",
        empresa="Clínica Bem Viver",
        cargo="Fundador",
        linkedin_url="https://linkedin.com/in/bruno-lima",
        provider_id="mock-bruno",
        sobre="Empreendedor na área de saúde, buscando digitalizar processos.",
        posts_recentes=["Como a tecnologia mudou a gestão da minha clínica."],
    ),
]


class MockProvider(LinkedInProvider):
    nome = "mock"

    def buscar_pessoas(self, termo: str, limite: int = 10) -> list[PerfilLinkedIn]:
        return _PERFIS_FAKE[:limite]

    def obter_perfil(self, linkedin_url: str) -> PerfilLinkedIn:
        for p in _PERFIS_FAKE:
            if p.linkedin_url == linkedin_url:
                return p
        return PerfilLinkedIn(nome="Perfil (simulado)", linkedin_url=linkedin_url)

    def seguir(self, linkedin_url: str, provider_id: str = "") -> bool:
        return True

    def enviar_convite(
        self, linkedin_url: str, mensagem: str, provider_id: str = ""
    ) -> bool:
        return True

    def enviar_mensagem(self, external_id: str, texto: str) -> bool:
        return True

    def publicar_post(self, texto: str, imagem_path: str = "") -> str:
        return "mock-urn:post:123"
