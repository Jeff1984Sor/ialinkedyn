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

BANCO DE PERGUNTAS & RESPOSTAS (sua ÚNICA base de verdade):
{{banco_qa}}

HISTÓRICO DA CONVERSA (mais antigo -> mais recente):
{{historico}}

NOVA MENSAGEM DO LEAD:
"{{mensagem_lead}}"

TAREFA: Escreva UMA resposta para o lead, em português do Brasil, no tom da marca.

COMO ESCREVER:
- Curta e natural: 2 a 5 frases, como mensagem de LinkedIn (não é e-mail formal).
- Nada de "Prezado", "Espero que esteja bem", textão ou linguagem robótica.
- Fale de resultado para o negócio dele, não de tecnologia.
- Quando fizer sentido, termine com UMA pergunta que abra a conversa
  (entender a dor vale mais do que empurrar proposta).

O QUE VOCÊ NÃO PODE FAZER (regras rígidas):
- NÃO invente preço, prazo, funcionalidade ou case que não esteja no banco acima.
- NÃO prometa prazo fixo (ex.: "fica pronto em 15 dias"). O prazo é sempre definido
  no orçamento, depois do diagnóstico.
- Se a pergunta não tiver resposta no banco, seja honesta: diga que vai confirmar
  ou convide para uma conversa rápida de diagnóstico. Preferir admitir a inventar.
- Não prometa desconto nem condição comercial por conta própria.

SE O LEAD DEMONSTRAR INTERESSE: convide para uma conversa rápida de diagnóstico.{{assinatura}}

Responda APENAS com o texto da mensagem (sem aspas, sem explicações, sem assunto).""",

    "cacador": """{{contexto_marca}}

PERFIL DO LEAD (dados reais do LinkedIn):
{{perfil}}

TAREFA: Escreva a PRIMEIRA abordagem para conectar com essa pessoa no LinkedIn.

ESTRUTURA (gancho -> prova -> convite):
1. GANCHO: comece citando algo específico e REAL do perfil dela — o cargo, a empresa,
   o segmento, algo do "sobre" ou de um post. Tem que ficar claro que você olhou o
   perfil, não é disparo em massa.
2. PROVA: conecte com o que a empresa resolve para alguém nessa situação. Se houver
   um case do mesmo segmento, mencione de leve.
3. CONVITE: termine com uma pergunta leve ou convite para conversar.

COMO ESCREVER:
- 2 a 4 frases. Curto. Português do Brasil, natural, como uma pessoa escreveria.
- Fale da dor/resultado do negócio dela, não das suas tecnologias.

PROIBIDO:
- Clichê de LinkedIn: "Cansado de...", "Você sabia que...", "Espero que esteja bem",
  "Venho por meio desta", elogio genérico ("adorei seu perfil!").
- Prometer preço, prazo fixo ou resultado numérico ("aumente 300% suas vendas").
- Tentar fechar venda na primeira mensagem. O objetivo aqui é abrir conversa.
- Inventar qualquer informação sobre a pessoa que não esteja no perfil acima.

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
