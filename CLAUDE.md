# claude.md — Memória do Projeto IALinkedyn

> Memória persistente do projeto. O Claude Code lê ao iniciar sessão nesta pasta. Manter atualizado ao fim de cada sessão.
>
> **Referência (NÃO clonar):** MayaPost (`C:\Users\JeffersonFernandes\Projetos\mayapost`) — automação de Instagram. O IALinkedyn só se **inspira na ideia**; não copia código. Foco 100% em **LinkedIn**.
>
> **Escopo:** **SINGLE-TENANT** — sistema para UMA empresa (a sua). SEM multi-tenant, SEM superadmin, SEM `tenant_id`. Login simples (um ou poucos usuários da mesma empresa).

---

## 1. O QUE É

Um **funcionário virtual de LinkedIn**, gerenciado 100% pelo **painel próprio** (o usuário NÃO opera dentro do LinkedIn nem fica logando). A conta do LinkedIn é conectada uma vez, via **provedor de API**, e daí em diante o painel controla tudo.

Ele **posta conteúdo**, **prospecta** (busca empresas/pessoas, segue, aborda), **responde o chat** com IA baseada num **Banco de Perguntas & Respostas**, e **aprende** com o uso.

---

## 1.1 IDENTIDADE (MayaCorp) — a IA deve respeitar

- **Empresa:** MayaCorp — **Fábrica de Software** (sistemas sob medida + automação/IA).
- **Funcionária virtual:** **Maya** (assina as mensagens).
- **Mensagem central:** **previsibilidade** — "prazo definido no orçamento e cumprido"; fim do "projeto eterno".
- ⚠️ **NUNCA** prometer prazo fixo de 15 dias. **NUNCA** inventar preço/prazo que não esteja no Banco de Q&A.
- **Portfólio:** Gestão (CRM, ERP, gestão de processos, sob medida; cases Studio de Pilates e Beach Tennis) · Premium (automações WhatsApp, n8n, IA — agentes e chatbots).
- **ICP:** donos/gestores de PMEs com dor de processo manual — clínicas/studios, academias/beach tennis, advocacia/contabilidade, empresas de serviços; decisor costuma já ter se queimado com projeto atrasado.
- **Tom:** profissional e próximo, PT-BR, frases curtas, fala de resultado de negócio (não de tecnologia), sem clichê de LinkedIn.
- **CTA:** conversa rápida de diagnóstico (15-20 min) · contato **mayacorp@mayacorp.com.br**

> Isso está semeado em `scripts/seed_marca.py` (roda `python -m scripts.seed_marca` para preencher a tela Marca/Voz).

---

## 2. MÓDULOS / FUNCIONALIDADES

**M1 — Conta & Conexão**
- Vincular conta(s) do LinkedIn ao painel (conecta 1x via provedor).

**M2 — Conteúdo**
- IA cria post → aprova → agenda → publica automático no feed.

**M3 — Prospecção (agente Caçador)**
- Buscar empresas/pessoas pelo ICP (perfil ideal).
- Seguir automaticamente alvos.
- Enviar convite + 1ª abordagem personalizada.

**M4 — Chat / Atendimento (agente Atendente)**
- Responder mensagens do chat com base no Banco de Q&A + tom da marca.
- Modos: aprovar-e-enviar OU automático (liga/desliga no painel).

**M5 — Cérebro & Aprendizado**
- Banco de Perguntas & Respostas (usuário cadastra; IA usa).
- Marca/Voz: descrição da empresa, tom, ICP, CTA.
- Aprendizado (4 loops): (a) correções do usuário viram conhecimento; (b) pergunta sem boa resposta vira nova Q&A; (c) mensagem que deu resultado vira exemplo preferido; (d) memória por lead (histórico/estágio).

---

## 3. FILOSOFIA DE SEGURANÇA (crítica — lição do MayaPost)

- A **API oficial do LinkedIn** cobre bem **postar no feed** (OAuth, se App aprovado); NÃO cobre DM 1:1 de prospecção nem seguir em massa.
- Para chat/prospecção/seguir usa-se um **provedor de API** (ver seção 5) que gerencia a sessão da conta.
- ⚠️ **Seguir automático e volume de convites/mensagens = ação de bot.** Risco de restrição/ban. Mitigar SEMPRE com: limites diários configuráveis, intervalos aleatórios (ritmo humano), respeitar os caps do provedor. Nunca "rajada".
- NUNCA robô headless próprio logando na conta 24/7 (pior caminho de ban). Sempre via provedor.
- Modo padrão do chat = aprovação humana; automático é opt-in.

---

## 3.1 FLUXO DE TRABALHO

- Edição **local** (VS Code + Claude Code). **NADA roda/testa na máquina local** — execução, banco e testes só na **VM (VPS prod1)** — hostname `servidor-prod1`. (O MayaPost mora no prod2; IALinkedyn é no prod1.)
- Deploy/atualização via git: `git pull → pip install -r requirements.txt → alembic upgrade head → (frontend) npm install && npm run build → restart systemd`.
- Não tentar subir servidor/Postgres local nem rodar a app localmente.

---

## 4. STACK (inspirada no MayaPost)

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic.
- **Banco:** PostgreSQL na VPS prod1, database `ialinkedyn`.
- **Worker:** APScheduler (jobs: publicar agendados, prospecção com ritmo, coletar mensagens novas, follow com limite diário).
- **IA:** **Google Gemini** (`google-genai`). Orquestração direta dos agentes.
- ⚠️ **Configuração é pelo PAINEL, não pelo `.env`.** Chaves de produto (Gemini, Unipile) e escolha do provedor ficam na tabela `app_config`, **criptografadas com Fernet**, editáveis na tela **Conexões**. O `.env` guarda só infra: `DATABASE_URL`, `JWT_SECRET`, `FERNET_KEY`, CORS.
- **Frontend:** Next.js + TS + Tailwind + shadcn/ui + TanStack Query + Recharts.
- **Auth:** JWT simples (single-tenant; sem tenant_id).
- **Config:** tudo em `.env`; tokens de terceiros criptografados com Fernet.

---

## 5. CAMADA DE CONEXÃO LINKEDIN (plugável)

Interface `LinkedInProvider` — o resto do sistema não sabe qual provedor está por baixo. Métodos previstos:
`conectar_conta`, `publicar_post`, `buscar_empresas`, `buscar_pessoas`, `seguir`, `enviar_convite`, `listar_conversas`, `listar_mensagens`, `enviar_mensagem`, `webhook_mensagem_nova`.

Implementações:
- **MockProvider** — simulado, para desenvolver o cérebro sem depender de contratação (FASE 1).
- **UnipileProvider** — provedor real recomendado. Cobre postar, conectar, buscar, seguir, convites e mensagens numa API só; tem webhooks (essencial para "chegou mensagem → IA responde"). Alternativa/plano B: **MyAgentMail** (mais barato, LinkedIn+email).

> Decisão: começar com Unipile. Trocar de provedor = trocar só esta camada.

---

## 6. MODELO DE DADOS (database `ialinkedyn`) — rascunho

- **user** — id, email, senha_hash, nome, ativo, criado_em (login simples).
- **linkedin_account** — id, nome, provider, external_account_id, status, token(Fernet), conectado_em.
- **knowledge_item** (Q&A) — id, pergunta, resposta, tags, categoria, ativo, criado_em.
- **brand_voice** — id, **nome_assistente** (nome da funcionária, ex. "Sofia"), **persona** (personalidade/estilo), **avatar_url** (opcional), **assina_mensagens** (bool), descricao_empresa, tom, icp, cta (registro único de config). O nome/persona da funcionária entra no prompt de todos os agentes e pode assinar mensagens.
- **lead** — id, nome, headline, empresa, cargo, linkedin_url, origem, status(NOVO|SEGUINDO|CONVIDADO|ABORDADO|RESPONDEU|QUALIFICADO|GANHO|PERDIDO), notas, criado_em.
- **conversation** — id, lead_id(FK), canal, external_id, criado_em.
- **message** — id, conversation_id(FK), autor(LEAD|EU|IA_RASCUNHO), conteudo, enviado_em/criado_em.
- **post** — id, texto, status(rascunho|aprovado|agendado|publicado|erro), agendado_para, publicado_em, external_urn, criado_em.
- **prompt_template** — id, chave, conteudo (prompts dos agentes, editáveis).
- **agent_run** — id, tipo, input, output_json(JSONB), status, criado_em (auditoria/aprendizado).
- **feedback / learning** — id, tipo(correcao|resultado), ref (message/post/lead), antes, depois, sinal, criado_em.
- **automation_settings** — limites diários (follows/convites/mensagens), horários, modo do chat (auto/manual).

> Histórico nunca sobrescrito. Tokens criptografados com Fernet.

---

## 7. AGENTES IA

| Agente | Função | Endpoint |
|---|---|---|
| ✍️ Criador | gera texto de post no tom da marca | `POST /agents/gerar-post` |
| 🎯 Caçador | busca alvos + gera 1ª abordagem a partir do perfil + ICP | `POST /agents/prospectar` |
| 💬 Atendente | responde uma mensagem usando Banco de Q&A + memória + tom | `POST /agents/responder` |
| ❤️ Engajador (fase 2) | sugere comentário para post de lead | `POST /agents/sugerir-engajamento` |

- Todos leem do cérebro: `knowledge_item` + `brand_voice` + exemplos vencedores + prompts editáveis.
- Toda geração salva em `agent_run`. Busca de Q&A: começar por palavra-chave/tags; evoluir p/ embeddings.

---

## 8. FRONTEND (telas)

- **Conexões** — vincular conta LinkedIn, status, limites de automação.
- **Conteúdo** — criar/aprovar/agendar posts (dispara Criador).
- **Prospecção** — definir ICP, buscar empresas/pessoas, fila de follow/convite (respeitando limites), abordagem.
- **Conversas / Inbox** — chat unificado; Atendente sugere/responde; liga/desliga automático.
- **Leads (CRM)** — funil por status.
- **Base de Conhecimento** — CRUD Q&A.
- **Marca / Voz** — nome da funcionária + persona + avatar (opcional) + se assina mensagens; empresa, tom, ICP, CTA.
- **Prompts** — editar prompts dos agentes.
- **Aprendizado** — lacunas detectadas, correções, o que está funcionando.

---

## 9. ORDEM DE EXECUÇÃO (uma etapa por vez, confirmar ao fim)

**Fase 0 — Fundação**
1. [ ] Estrutura + requirements.txt + .env.example + .gitignore
2. [ ] core (config/database/security/deps) + DB `ialinkedyn`
3. [ ] user + auth JWT simples + migration inicial

**Fase 1 — Cérebro + Chat (prioridade máxima)**
4. [ ] Models: knowledge_item, brand_voice, lead, conversation, message, feedback + migration
5. [ ] CRUD: knowledge, brand, leads, conversations
6. [ ] Camada LinkedInProvider + MockProvider
7. [ ] Agente Atendente (`/agents/responder`) + busca de Q&A + memória
8. [ ] Aprendizado v1 (correção vira conhecimento; pergunta nova vira Q&A)
9. [ ] Frontend: Inbox, Leads, Base de Conhecimento, Marca, Prompts

**Fase 2 — Prospecção & Conteúdo**
10. [ ] Caçador (buscar empresas/pessoas + seguir + convite) com limites/ritmo + Worker
11. [ ] Criador + agendar/publicar post + Worker

**Fase 3 — Real & Deploy**
12. [ ] UnipileProvider (liga o real: postar, conectar, buscar, seguir, mensagens + webhooks)
13. [ ] Deploy VPS **prod1** (systemd + Nginx + subdomínio `ialinkedyn.mayacorp.com.br` + DB) — receita de deploy = molde MayaPost.
    - ⚠️ **prod1 é compartilhada. NÃO duplicar infra.** REUSAR: Postgres (só criar DB `ialinkedyn`), Nginx (só site novo), certbot, runtimes. EXCLUSIVO/isolado: DB `ialinkedyn`, portas próprias, serviços `ialinkedyn-*`, subdomínio, venv próprio.
    - **Auditoria do prod1 (feita 2026-07-13):** portas 8020/8021/3020/3021 LIVRES; DBs existentes só `sistemarca` (owner admin) + padrão — sem `mayapost` aqui; nenhum serviço maya/pilates/flic/beach; Nginx tem só o site `rca_final`. → usar **DB `ialinkedyn`**, **portas 8021/3021**, serviços `ialinkedyn-*` sem colisão.

**Regra full-stack:** toda feature tem backend E frontend.

---

## 10. SEGURANÇA

- Nada de segredo hardcoded — tudo em `.env` fora do git.
- Tokens de terceiros criptografados com Fernet.
- Validar inputs com Pydantic.
- Limites de automação (follow/convite/mensagem) obrigatórios e configuráveis.

---

## 11. DECISÕES EM ABERTO

- [ ] Contratar provedor (Unipile recomendado) — depende do usuário; MockProvider destrava o desenvolvimento antes disso.
- [x] LLM dos agentes = **Google Gemini** (`google-genai`, `GEMINI_MODEL` configurável).
- [x] Servidor = **prod1**. Portas 8021/3021 confirmadas livres (auditoria 2026-07-13). Falta: subdomínio + DNS.
- [ ] Acento visual (petróleo/roxo do Maya x azul LinkedIn).

---

## LOG DE SESSÕES

- **Sessão 0 (2026-07-13):** Concepção e escopo. Definido: single-tenant; gerenciado 100% pelo painel próprio (sem logar no LinkedIn); conexão via provedor de API (Unipile recomendado; MyAgentMail plano B) numa camada plugável (MockProvider p/ desenvolver antes de contratar). Módulos: conectar conta, postar automático, buscar empresas/pessoas + seguir automático (com limites/ritmo anti-ban), responder chat com Banco de Q&A, e aprendizado (4 loops). MVP começa pela Fase 1 (cérebro + chat). Repo zerado: github.com/Jeff1984Sor/ialinkedyn. **Nenhum código ainda — só o norte (este CLAUDE.md).**
