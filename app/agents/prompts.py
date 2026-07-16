"""Prompts dos agentes (padrões) + montagem do contexto do cérebro.

Os textos aqui são os PADRÕES. O usuário pode sobrescrever cada um pela
tela de Prompts (tabela prompt_template). Os marcadores {{...}} são
substituídos em tempo de execução.
"""
from __future__ import annotations

from app.models.brand import BrandVoice
from app.models.knowledge import KnowledgeItem

# --- Chaves e rótulos (aparecem na tela de Prompts) ---
LABELS: dict[str, str] = {
    "atendente": "💬 Atendente — responder mensagens do chat",
    "cacador": "🎯 Caçador — 1ª abordagem personalizada",
}

# Marcadores disponíveis em cada prompt (mostrados na UI como ajuda)
PLACEHOLDERS: dict[str, list[str]] = {
    "atendente": ["{{contexto_marca}}", "{{banco_qa}}", "{{historico}}", "{{mensagem_lead}}", "{{assinatura}}"],
    "cacador": ["{{contexto_marca}}", "{{perfil}}"],
}

DEFAULTS: dict[str, str] = {
    "atendente": """{{contexto_marca}}

BANCO DE PERGUNTAS & RESPOSTAS (use como base de verdade; não invente fatos):
{{banco_qa}}

HISTÓRICO DA CONVERSA (mais antigo -> mais recente):
{{historico}}

NOVA MENSAGEM DO LEAD:
"{{mensagem_lead}}"

TAREFA: Escreva UMA resposta para o lead, em português do Brasil, no tom da marca.
Regras:
- Baseie-se no banco de Q&A acima. Se não houver resposta adequada, seja honesta e ofereça encaminhar para um humano.
- Soe natural e humana, nunca robótica. Curta e objetiva (2 a 5 frases).
- Não invente preços, prazos ou fatos que não estejam no banco.{{assinatura}}

Responda APENAS com o texto da mensagem (sem aspas, sem explicações).""",

    "cacador": """{{contexto_marca}}

PERFIL DO LEAD (dados reais do LinkedIn):
{{perfil}}

TAREFA: Escreva uma primeira abordagem PERSONALIZADA para conectar com essa pessoa no LinkedIn.
Regras:
- Cite algo específico e real do perfil dela (cargo, empresa, um post, o "sobre").
- Conecte com o que a nossa empresa oferece ao público ideal.
- Tom da marca, português do Brasil, curta (2 a 4 frases), nada de spam genérico.
- Termine com uma pergunta ou convite leve (não force venda na primeira mensagem).

Responda APENAS com o texto da mensagem (sem aspas, sem explicações).""",
}


def contexto_marca(brand: BrandVoice) -> str:
    nome = brand.nome_assistente or "Assistente"
    linhas = [f"Você é {nome}, a assistente virtual da empresa no LinkedIn."]
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
    return "\n".join(
        f"{i}. Pergunta: {k.pergunta}\n   Resposta padrão: {k.resposta}"
        for i, k in enumerate(itens, 1)
    )


def _preencher(template: str, valores: dict[str, str]) -> str:
    """Substitui os marcadores {{chave}} — usa replace (não .format) para
    não quebrar com chaves { } no conteúdo do usuário."""
    texto = template
    for chave, valor in valores.items():
        texto = texto.replace("{{" + chave + "}}", valor)
    return texto


def montar_atendente(
    template: str,
    brand: BrandVoice,
    qa: list[KnowledgeItem],
    historico: str,
    mensagem_lead: str,
) -> str:
    assinatura = ""
    if brand.assina_mensagens and brand.nome_assistente:
        assinatura = f"\n- Assine a mensagem como '{brand.nome_assistente}' ao final."
    return _preencher(
        template,
        {
            "contexto_marca": contexto_marca(brand),
            "banco_qa": contexto_qa(qa),
            "historico": historico or "(sem histórico)",
            "mensagem_lead": mensagem_lead,
            "assinatura": assinatura,
        },
    )


def montar_cacador(template: str, brand: BrandVoice, perfil_texto: str) -> str:
    return _preencher(
        template,
        {
            "contexto_marca": contexto_marca(brand),
            "perfil": perfil_texto,
        },
    )


def prompt_melhorar(chave: str, conteudo_atual: str, instrucao: str) -> str:
    """Meta-prompt: pede à IA para reescrever um prompt de agente."""
    marcadores = ", ".join(PLACEHOLDERS.get(chave, []))
    return f"""Você é um especialista em engenharia de prompts para agentes de IA.

Abaixo está o PROMPT ATUAL de um agente chamado "{LABELS.get(chave, chave)}".

PROMPT ATUAL:
---
{conteudo_atual}
---

PEDIDO DO USUÁRIO (o que ele quer mudar):
"{instrucao}"

REGRAS OBRIGATÓRIAS:
- Reescreva o prompt atendendo ao pedido, mantendo a estrutura e a clareza.
- PRESERVE EXATAMENTE todos estes marcadores, sem renomear nem remover: {marcadores}
- Mantenha o texto em português do Brasil.
- Não adicione comentários, explicações ou markdown de code fence.

Responda APENAS com o novo prompt completo."""
