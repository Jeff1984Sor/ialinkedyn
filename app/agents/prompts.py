"""Prompts dos agentes + montagem do contexto do cérebro."""
from __future__ import annotations

from app.models.brand import BrandVoice
from app.models.knowledge import KnowledgeItem


def contexto_marca(brand: BrandVoice) -> str:
    nome = brand.nome_assistente or "Assistente"
    linhas = [
        f"Você é {nome}, a assistente virtual da empresa no LinkedIn.",
    ]
    if brand.persona:
        linhas.append(f"Personalidade/estilo: {brand.persona}")
    if brand.descricao_empresa:
        linhas.append(f"Sobre a empresa: {brand.descricao_empresa}")
    if brand.tom:
        linhas.append(f"Tom de voz: {brand.tom}")
    if brand.icp:
        linhas.append(f"Público ideal (ICP): {brand.icp}")
    if brand.cta:
        linhas.append(f"Chamada para ação (CTA) preferida: {brand.cta}")
    return "\n".join(linhas)


def contexto_qa(itens: list[KnowledgeItem]) -> str:
    if not itens:
        return "(Nenhuma pergunta/resposta cadastrada ainda no banco de conhecimento.)"
    blocos = []
    for i, k in enumerate(itens, 1):
        blocos.append(f"{i}. Pergunta: {k.pergunta}\n   Resposta padrão: {k.resposta}")
    return "\n".join(blocos)


def prompt_atendente(
    brand: BrandVoice,
    qa: list[KnowledgeItem],
    historico: str,
    mensagem_lead: str,
) -> str:
    assina = ""
    if brand.assina_mensagens and brand.nome_assistente:
        assina = f"\n- Assine a mensagem como '{brand.nome_assistente}' ao final."
    return f"""{contexto_marca(brand)}

BANCO DE PERGUNTAS & RESPOSTAS (use como base de verdade; não invente fatos):
{contexto_qa(qa)}

HISTÓRICO DA CONVERSA (mais antigo -> mais recente):
{historico or "(sem histórico)"}

NOVA MENSAGEM DO LEAD:
"{mensagem_lead}"

TAREFA: Escreva UMA resposta para o lead, em português do Brasil, no tom da marca.
Regras:
- Baseie-se no banco de Q&A acima. Se não houver resposta adequada, seja honesta e ofereça encaminhar para um humano.
- Soe natural e humana, nunca robótica. Curta e objetiva (2 a 5 frases).
- Não invente preços, prazos ou fatos que não estejam no banco.{assina}

Responda APENAS com o texto da mensagem (sem aspas, sem explicações)."""


def prompt_cacador(brand: BrandVoice, perfil_texto: str) -> str:
    return f"""{contexto_marca(brand)}

PERFIL DO LEAD (dados reais do LinkedIn):
{perfil_texto}

TAREFA: Escreva uma primeira abordagem PERSONALIZADA para conectar com essa pessoa no LinkedIn.
Regras:
- Cite algo específico e real do perfil dela (cargo, empresa, um post, o "sobre").
- Conecte com o que a nossa empresa oferece ao público ideal.
- Tom da marca, português do Brasil, curta (2 a 4 frases), nada de spam genérico.
- Termine com uma pergunta ou convite leve (não force venda na primeira mensagem).

Responda APENAS com o texto da mensagem (sem aspas, sem explicações)."""
