"""Semeia o Banco de Perguntas & Respostas com o conteúdo da MayaCorp.

Uso (na VM, com a .venv ativa):
    python -m scripts.seed_qa

Idempotente: não duplica — se a pergunta já existir, atualiza a resposta.

Regras de marca respeitadas em todas as respostas:
  - previsibilidade (prazo definido no orçamento e cumprido)
  - NUNCA prometer prazo fixo de 15 dias
  - NUNCA cravar preço (sempre diagnóstico -> orçamento fechado)
  - tom próximo, PT-BR, foco em resultado de negócio
"""
from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeItem

# (categoria, tags, pergunta, resposta)
QA: list[tuple[str, str, str, str]] = [
    # ---------------------------------------------------------------- Preço
    ("Preços", "preço, valor, custo", "Quanto custa um sistema?",
     "Depende bastante do que a sua operação precisa — um CRM enxuto e um ERP completo são projetos bem diferentes. "
     "O que a gente faz é um diagnóstico rápido (uns 20 minutos) pra entender o escopo e te devolver um orçamento fechado, "
     "com prazo definido. Sem surpresa no meio do caminho. Quer marcar essa conversa?"),

    ("Preços", "preço, orçamento", "Vocês têm uma tabela de preços?",
     "Não trabalhamos com tabela fixa, porque cada operação tem um desenho diferente — cobrar por pacote pronto normalmente "
     "significa o cliente pagar por coisa que não usa. Depois de entender seu processo, mandamos um orçamento fechado com escopo "
     "e prazo. Posso te chamar pra um diagnóstico rápido?"),

    ("Preços", "preço, barato, caro", "É caro?",
     "Justo é a palavra melhor. O orçamento é fechado, então você sabe exatamente quanto vai custar antes de começar — sem aquele "
     "'vai passar um pouquinho' que todo mundo já viveu. E a gente dimensiona pelo que faz sentido pro seu momento. Vale conversarmos "
     "pra eu te dar um número real em vez de você ficar no escuro?"),

    ("Preços", "pagamento, parcelamento", "Como funciona o pagamento?",
     "A gente combina isso junto com o escopo, normalmente atrelando as parcelas às etapas de entrega. Assim você acompanha o projeto "
     "andando e o pagamento segue o mesmo ritmo. Os detalhes ficam claros no orçamento."),

    ("Preços", "mensalidade, recorrência", "Tem mensalidade depois de pronto?",
     "Depende do que você contratar. Sistema entregue é seu. Se quiser que a gente cuide de hospedagem, suporte e evolução contínua, "
     "aí existe um plano mensal — mas é opcional e a gente deixa isso transparente no orçamento."),

    # ---------------------------------------------------------------- Prazo
    ("Prazos", "prazo, tempo, entrega", "Em quanto tempo fica pronto?",
     "O prazo sai junto com o orçamento, depois que a gente entende o escopo — e é um compromisso, não uma estimativa solta. "
     "Esse é justamente nosso diferencial: prazo definido no orçamento e cumprido. Projeto pequeno anda rápido, projeto grande "
     "a gente fatia em entregas. Me conta o que você precisa que eu te dou uma noção real."),

    ("Prazos", "prazo, atraso", "E se atrasar?",
     "Nosso compromisso é o prazo acordado no orçamento — é o que nos diferencia de quem entra no 'projeto eterno'. "
     "A gente trabalha com entregas parciais justamente pra você enxergar o andamento e não descobrir problema só no final."),

    ("Prazos", "urgente, rápido", "Preciso pra ontem, dá pra acelerar?",
     "Dá pra priorizar sim. O caminho costuma ser começar por uma primeira versão com o essencial e evoluir depois — assim você já "
     "coloca em uso rápido em vez de esperar tudo ficar pronto. Me conta qual é a urgência que a gente desenha o corte certo."),

    ("Prazos", "etapas, fases", "Vocês entregam por partes?",
     "Sim, é assim que preferimos trabalhar. A gente fatia em entregas para você usar e validar antes de seguir. Isso reduz risco "
     "dos dois lados e evita aquela surpresa de receber no final algo diferente do que você imaginava."),

    # ---------------------------------------------------------------- Processo
    ("Processo", "como funciona, início", "Como funciona o processo de vocês?",
     "É bem direto: (1) conversa de diagnóstico pra entender sua operação, (2) proposta com escopo, prazo e valor fechados, "
     "(3) desenvolvimento com entregas parciais pra você acompanhar, (4) entrega e ajustes. Sem etapa surpresa e sem prazo elástico."),

    ("Processo", "reunião, diagnóstico", "Como marco uma conversa?",
     "É só me dizer um horário que funciona pra você — costuma levar uns 15 a 20 minutos. Se preferir, escreve pra "
     "mayacorp@mayacorp.com.br. Nessa conversa a ideia é entender sua operação, não te empurrar nada."),

    ("Processo", "requisitos, escopo", "Preciso ter tudo definido antes?",
     "Não precisa. Boa parte dos clientes chega com a dor, não com a especificação — e ajudar a transformar isso em escopo faz parte "
     "do nosso trabalho. Você traz o problema, a gente desenha a solução junto."),

    ("Processo", "acompanhamento", "Consigo acompanhar o andamento?",
     "Sim. Você acompanha por entregas parciais e conversas de alinhamento ao longo do projeto. A ideia é que você nunca fique "
     "no escuro sem saber em que pé está."),

    ("Processo", "mudança, alteração", "E se eu precisar mudar algo no meio?",
     "Acontece com frequência e é normal. Ajustes pequenos entram no fluxo; mudanças que alteram o escopo a gente conversa e "
     "repactua de forma transparente — nunca vira conta surpresa no final."),

    ("Processo", "reunião presencial, online", "Atendem presencialmente?",
     "Trabalhamos remoto, o que deixa o processo mais ágil e atende cliente de qualquer lugar. As conversas são por vídeo e "
     "funcionam muito bem."),

    # ---------------------------------------------------------------- Produtos
    ("Produtos", "crm, vendas", "Vocês fazem CRM?",
     "Fazemos, e sob medida — que é diferente de assinar um CRM de prateleira e ter que encaixar seu processo nele. "
     "A gente modela o funil do seu jeito. Como é seu processo comercial hoje?"),

    ("Produtos", "erp, gestão", "Vocês desenvolvem ERP?",
     "Sim. Sistemas de gestão são o nosso forte — financeiro, estoque, ordens de serviço, o que a operação exigir. "
     "Me conta o que hoje é feito na planilha que eu te digo como costumamos resolver."),

    ("Produtos", "sob medida, personalizado", "É sistema pronto ou feito do zero?",
     "Feito sob medida pra sua operação. A gente reaproveita o que já domina pra ganhar velocidade, mas o sistema segue o seu "
     "processo — e não o contrário."),

    ("Produtos", "gestão de processos, workflow", "Vocês fazem gestão de processos?",
     "Fazemos. É comum a gente mapear um processo que hoje vive em planilha, e-mail e WhatsApp e transformar num fluxo único, "
     "com responsável e prazo em cada etapa. Qual processo mais trava aí?"),

    ("Produtos", "app, aplicativo, mobile", "Vocês fazem aplicativo?",
     "Desenvolvemos sistemas que funcionam bem no celular. Se a necessidade for realmente um app de loja, a gente avalia junto se "
     "compensa — muitas vezes um sistema web responsivo resolve com menos custo."),

    ("Produtos", "site, landing page", "Vocês fazem site?",
     "Nosso foco é sistema e automação, não site institucional. Se for site com alguma inteligência por trás (área do cliente, "
     "integração, cadastro), aí entra no nosso escopo. Me conta o que você tem em mente."),

    ("Produtos", "integração, api", "Consegue integrar com o sistema que já uso?",
     "Na maioria dos casos sim — integração é parte grande do que fazemos. Depende do sistema ter uma forma de conexão (API ou "
     "exportação). Me diz qual sistema é que eu te confirmo."),

    ("Produtos", "migração, dados", "Dá pra migrar meus dados atuais?",
     "Dá sim, é uma etapa comum do projeto. Normalmente trazemos os dados que estão em planilha ou no sistema antigo pra você "
     "não começar do zero."),

    # ---------------------------------------------------------------- Automação / IA
    ("Automação e IA", "whatsapp, automação", "Vocês fazem automação de WhatsApp?",
     "Fazemos — é um dos serviços que mais gera resultado rápido. Dá pra automatizar atendimento, confirmação de agendamento, "
     "cobrança e follow-up. O que mais consome tempo da sua equipe hoje no WhatsApp?"),

    ("Automação e IA", "ia, inteligência artificial", "Vocês trabalham com IA?",
     "Sim, é nossa linha Premium: agentes e chatbots que atendem, respondem dúvidas e ajudam a vender — treinados com o "
     "conhecimento do seu negócio. Inclusive esse tipo de solução é o que estou fazendo aqui nesta conversa."),

    ("Automação e IA", "chatbot, atendimento", "Chatbot não deixa o atendimento robótico?",
     "Deixa quando é aquele menu de 'digite 1'. A gente trabalha diferente: o agente é alimentado com o conhecimento real do "
     "negócio e conversa de forma natural — e sempre com a opção de passar pra um humano quando faz sentido."),

    ("Automação e IA", "n8n, integração", "O que é n8n?",
     "É uma ferramenta de automação que conecta sistemas — tipo 'quando entrar um pedido aqui, cria a tarefa ali e avisa no "
     "WhatsApp'. Usamos bastante pra ligar as pontas sem precisar reescrever tudo."),

    ("Automação e IA", "automação, economia", "O que dá pra automatizar no meu negócio?",
     "Normalmente o que é repetitivo: confirmação de agendamento, cobrança, follow-up de orçamento, envio de relatório, "
     "cadastro que alguém digita duas vezes. Me conta como é seu dia a dia que eu aponto onde costuma ter o maior ganho."),

    # ---------------------------------------------------------------- Cases
    ("Cases", "case, exemplo, portfólio", "Vocês têm cases?",
     "Temos. Dois que gosto de citar: um sistema completo pra Studio de Pilates (agenda, alunos, financeiro) e outro pra arena de "
     "Beach Tennis. Além de CRMs e ERPs sob medida. Quer que eu te conte o que resolvemos em algum desses?"),

    ("Cases", "pilates, clínica, studio", "Vocês já fizeram algo pra clínica ou studio?",
     "Já — temos case de Studio de Pilates, com agenda, controle de alunos, planos e financeiro num sistema só. "
     "É um segmento que conhecemos bem. Sua operação é parecida?"),

    ("Cases", "academia, beach tennis, esporte", "Atendem academias e arenas esportivas?",
     "Sim, temos case de Beach Tennis — reserva de quadra, mensalidade, controle de alunos. A dor costuma ser a mesma: "
     "agenda no caderno ou no WhatsApp e dinheiro escapando."),

    ("Cases", "advocacia, contabilidade", "Atendem escritórios de advocacia ou contabilidade?",
     "Atendemos. É um perfil que se beneficia muito de gestão de processos e automação — prazos, documentos e follow-up "
     "com cliente. Como é a rotina do seu escritório hoje?"),

    ("Cases", "segmento, nicho", "Vocês atendem meu segmento?",
     "Trabalhamos com pequenas e médias empresas de vários setores — saúde, esporte, serviços, jurídico, comércio. O que importa "
     "mais que o segmento é o tipo de dor: processo manual, planilha demais, retrabalho. Me conta o seu caso?"),

    # ---------------------------------------------------------------- Objeções
    ("Objeções", "objeção, desconfiança", "Já me queimei com desenvolvedor que sumiu",
     "Infelizmente é uma história que a gente escuta bastante — e foi por causa dela que estruturamos a MayaCorp como fábrica, "
     "com prazo fechado no orçamento e entregas parciais. Você acompanha o projeto andando em vez de esperar meses por uma promessa."),

    ("Objeções", "objeção, planilha", "Minha planilha funciona, por que trocar?",
     "Se está funcionando, ótimo — planilha resolve muita coisa. O problema costuma aparecer quando cresce: duas pessoas editando, "
     "dado desatualizado, retrabalho. Se você ainda não sente essa dor, talvez não seja a hora. Sente?"),

    ("Objeções", "objeção, equipe, adaptação", "Minha equipe vai conseguir usar?",
     "Essa é uma preocupação legítima e a gente leva a sério. Como o sistema é feito em cima do processo que a equipe já faz, "
     "a curva é bem menor do que num sistema de prateleira. E acompanhamos a fase de adaptação."),

    ("Objeções", "objeção, tamanho, pequeno", "Minha empresa é pequena, vale a pena?",
     "Vale quando existe processo repetitivo consumindo tempo — e isso acontece em empresa de qualquer tamanho. Para operações "
     "menores costumamos começar com um escopo enxuto que já resolve a dor principal."),

    ("Objeções", "objeção, momento", "Agora não é um bom momento",
     "Sem problema, entendo. Posso te mandar uma mensagem mais pra frente? E se quiser, deixo meu contato pra quando fizer "
     "sentido: mayacorp@mayacorp.com.br"),

    ("Objeções", "objeção, concorrente", "Já tenho um sistema, por que trocar?",
     "Nem sempre trocar é o melhor caminho — às vezes o ganho está em integrar ou automatizar em volta do que você já tem. "
     "Me conta o que o sistema atual não resolve que eu te digo com honestidade se vale mexer."),

    # ---------------------------------------------------------------- Suporte / contrato
    ("Suporte", "suporte, manutenção", "Tem suporte depois de entregue?",
     "Tem. Após a entrega existe um período de acompanhamento para ajustes, e você pode contratar suporte e evolução contínua "
     "se quiser que a gente siga cuidando do sistema."),

    ("Suporte", "bug, erro, garantia", "E se aparecer um erro depois?",
     "Correção de defeito do que foi entregue é nossa responsabilidade — não é serviço extra. A gente não entrega e desaparece."),

    ("Suporte", "treinamento", "Vocês treinam a equipe?",
     "Sim, a passagem de conhecimento faz parte da entrega. Não adianta o sistema ser bom e ninguém saber usar."),

    ("Contrato", "contrato, formalização", "Como é formalizado?",
     "Com contrato e proposta detalhando escopo, prazo e valor. Tudo o que combinamos fica escrito — é o que dá segurança pros dois lados."),

    ("Contrato", "propriedade, código", "O sistema fica sendo meu?",
     "Fica. O que desenvolvemos pra você é seu — isso fica claro em contrato. Você não fica refém da gente."),

    ("Contrato", "nda, sigilo", "Vocês assinam NDA?",
     "Assinamos sem problema. Lidar com informação sensível de cliente faz parte do nosso trabalho."),

    # ---------------------------------------------------------------- Técnico
    ("Tecnologia", "tecnologia, stack", "Que tecnologias vocês usam?",
     "Trabalhamos com tecnologias modernas e consolidadas de mercado, escolhidas conforme o projeto — nada exótico que te deixe "
     "preso. Se quiser entrar no detalhe técnico, consigo trazer alguém do time pra conversar."),

    ("Tecnologia", "hospedagem, nuvem", "Onde o sistema fica hospedado?",
     "Normalmente em nuvem, com o custo de infraestrutura transparente no orçamento. Se você já tem um ambiente ou preferência, "
     "a gente se adapta."),

    ("Tecnologia", "segurança, dados, lgpd", "E a segurança dos dados?",
     "Levamos a sério: acesso controlado por usuário, dados sensíveis protegidos e boas práticas de segurança no desenvolvimento. "
     "Se o seu caso tiver exigência específica de LGPD, tratamos isso no escopo."),

    ("Tecnologia", "backup", "Tem backup?",
     "Tem. Rotina de backup faz parte de qualquer projeto sério — e a gente combina a frequência conforme a criticidade da sua operação."),

    # ---------------------------------------------------------------- Institucional
    ("Institucional", "empresa, quem somos", "Quem é a MayaCorp?",
     "Somos uma Fábrica de Software: desenvolvemos sistemas sob medida e soluções de automação e IA para pequenas e médias empresas. "
     "Nosso compromisso central é previsibilidade — prazo definido no orçamento e cumprido."),

    ("Institucional", "diferencial, por que", "Por que vocês e não outro?",
     "Pelo que mais dói em projeto de software: prazo. A gente fecha prazo no orçamento e cumpre, com entregas parciais pra você "
     "acompanhar. Some a isso a linha de automação e IA, que faz o sistema não só organizar mas também escalar o atendimento."),

    ("Institucional", "contato", "Como falo com vocês?",
     "Pode falar comigo por aqui mesmo, ou escrever pra mayacorp@mayacorp.com.br. Se preferir, marco uma conversa rápida de "
     "diagnóstico com o time."),

    ("Institucional", "tamanho, time", "Vocês são uma equipe grande?",
     "Somos uma fábrica estruturada em time — não é um freelancer sozinho, que é justamente o que costuma gerar o risco de o "
     "projeto parar quando a pessoa some."),
]


def main() -> None:
    db = SessionLocal()
    criados = atualizados = 0
    try:
        for categoria, tags, pergunta, resposta in QA:
            existente = db.scalar(
                select(KnowledgeItem).where(KnowledgeItem.pergunta == pergunta)
            )
            if existente:
                existente.resposta = resposta
                existente.categoria = categoria
                existente.tags = tags
                existente.ativo = True
                atualizados += 1
            else:
                db.add(
                    KnowledgeItem(
                        pergunta=pergunta,
                        resposta=resposta,
                        categoria=categoria,
                        tags=tags,
                        ativo=True,
                    )
                )
                criados += 1
        db.commit()
        print(f"Banco de Q&A semeado: {criados} criadas, {atualizados} atualizadas.")
        print(f"Total no script: {len(QA)} perguntas.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
