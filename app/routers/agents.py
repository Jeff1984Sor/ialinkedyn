"""Agentes de IA: Atendente (responder) e Caçador (prospectar)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import prompt_store
from app.agents.prompts import montar_atendente, montar_cacador
from app.core.deps import get_current_user, get_db
from app.models.conversation import Conversation, Message
from app.models.enums import MessageAuthor
from app.models.lead import Lead
from app.models.user import User
from app.providers.base import PerfilLinkedIn
from app.providers.factory import get_provider
from app.schemas.agent import (
    BuscarRequest,
    BuscarResponse,
    ImportarRequest,
    ImportarResponse,
    PerfilEncontrado,
    ProspectarRequest,
    ProspectarResponse,
    ResponderRequest,
    ResponderResponse,
)
from app.services.brand import get_or_create_brand
from app.services.config_service import get_provider_name
from app.services.ia import gerar
from app.services.knowledge_search import buscar_relevantes

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/responder", response_model=ResponderResponse)
def responder(
    dados: ResponderRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResponderResponse:
    """Atendente: gera uma resposta para a conversa usando o Banco de Q&A."""
    conversa = db.get(Conversation, dados.conversation_id)
    if not conversa:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    # Descobre a mensagem do lead a responder
    mensagem_lead = dados.mensagem_lead
    if not mensagem_lead:
        ultimas_do_lead = [m for m in conversa.mensagens if m.autor == MessageAuthor.LEAD.value]
        if ultimas_do_lead:
            mensagem_lead = ultimas_do_lead[-1].conteudo
    if not mensagem_lead:
        raise HTTPException(status_code=400, detail="Não há mensagem do lead para responder.")

    brand = get_or_create_brand(db)
    qa = buscar_relevantes(db, mensagem_lead, limite=5)

    historico = "\n".join(
        f"[{m.autor}] {m.conteudo}" for m in conversa.mensagens
    )

    template = prompt_store.resolver(db, "atendente")
    prompt = montar_atendente(template, brand, qa, historico, mensagem_lead)
    resposta = gerar(db, prompt)

    if dados.salvar_rascunho:
        rascunho = Message(
            conversation_id=conversa.id,
            autor=MessageAuthor.IA_RASCUNHO.value,
            conteudo=resposta,
        )
        db.add(rascunho)
        db.commit()

    return ResponderResponse(
        resposta=resposta,
        qa_usadas=[k.pergunta for k in qa],
    )


@router.post("/prospectar", response_model=ProspectarResponse)
def prospectar(
    dados: ProspectarRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProspectarResponse:
    """Caçador: gera 1ª abordagem personalizada a partir do perfil + ICP."""
    brand = get_or_create_brand(db)

    perfil_texto = dados.perfil_texto or ""
    resumo = ""

    if dados.linkedin_url and not perfil_texto:
        provider = get_provider(db)
        perfil = provider.obter_perfil(dados.linkedin_url)
        perfil_texto = _perfil_para_texto(perfil)
        resumo = f"{perfil.nome} — {perfil.headline}"
    elif dados.lead_id and not perfil_texto:
        lead = db.get(Lead, dados.lead_id)
        if lead:
            perfil_texto = (
                f"Nome: {lead.nome}\nHeadline: {lead.headline}\n"
                f"Empresa: {lead.empresa}\nCargo: {lead.cargo}\nNotas: {lead.notas}"
            )
            resumo = f"{lead.nome} — {lead.headline}"

    if not perfil_texto.strip():
        raise HTTPException(
            status_code=400,
            detail="Informe um linkedin_url, um lead_id ou um perfil_texto.",
        )

    template = prompt_store.resolver(db, "cacador")
    prompt = montar_cacador(template, brand, perfil_texto)
    abordagem = gerar(db, prompt)
    return ProspectarResponse(abordagem=abordagem, perfil_resumo=resumo)


@router.post("/buscar", response_model=BuscarResponse)
def buscar(
    dados: BuscarRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BuscarResponse:
    """Caçador: busca pessoas no LinkedIn pelo ICP (ou por um termo livre)."""
    brand = get_or_create_brand(db)
    termo = (dados.termo or "").strip() or (brand.icp or "").strip()
    if not termo:
        raise HTTPException(
            status_code=400,
            detail=(
                "Informe o que buscar, ou cadastre seu Público Ideal (ICP) "
                "em Marca / Voz para o Caçador usar."
            ),
        )

    provider = get_provider(db)
    encontrados = provider.buscar_pessoas(termo, limite=dados.limite)

    # marca quem já existe no CRM (evita importar duplicado)
    urls_existentes = {
        u for (u,) in db.execute(select(Lead.linkedin_url).where(Lead.linkedin_url != "")).all()
    }

    perfis = [
        PerfilEncontrado(
            nome=p.nome,
            headline=p.headline,
            empresa=p.empresa,
            cargo=p.cargo,
            linkedin_url=p.linkedin_url,
            sobre=p.sobre,
            posts_recentes=list(p.posts_recentes),
            ja_importado=bool(p.linkedin_url and p.linkedin_url in urls_existentes),
        )
        for p in encontrados
    ]

    nome_provider = get_provider_name(db)
    return BuscarResponse(
        termo_usado=termo,
        provider=nome_provider,
        simulado=(nome_provider == "mock"),
        perfis=perfis,
    )


@router.post("/importar-leads", response_model=ImportarResponse)
def importar_leads(
    dados: ImportarRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ImportarResponse:
    """Importa os perfis encontrados como Leads no CRM (sem duplicar)."""
    urls_existentes = {
        u for (u,) in db.execute(select(Lead.linkedin_url).where(Lead.linkedin_url != "")).all()
    }

    novos: list[Lead] = []
    ignorados = 0
    for p in dados.perfis:
        if p.linkedin_url and p.linkedin_url in urls_existentes:
            ignorados += 1
            continue
        lead = Lead(
            nome=p.nome or "(sem nome)",
            headline=p.headline,
            empresa=p.empresa,
            cargo=p.cargo,
            linkedin_url=p.linkedin_url,
            origem="Busca LinkedIn",
            status="NOVO",
            notas=p.sobre,
        )
        db.add(lead)
        novos.append(lead)
        if p.linkedin_url:
            urls_existentes.add(p.linkedin_url)

    db.commit()
    for lead in novos:
        db.refresh(lead)

    return ImportarResponse(
        importados=len(novos),
        ignorados=ignorados,
        lead_ids=[l.id for l in novos],
    )


def _perfil_para_texto(p: PerfilLinkedIn) -> str:
    linhas = [
        f"Nome: {p.nome}",
        f"Headline: {p.headline}",
        f"Empresa: {p.empresa}",
        f"Cargo: {p.cargo}",
    ]
    if p.sobre:
        linhas.append(f"Sobre: {p.sobre}")
    if p.posts_recentes:
        linhas.append("Posts recentes: " + " | ".join(p.posts_recentes))
    return "\n".join(linhas)
