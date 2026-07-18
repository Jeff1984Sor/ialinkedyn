"""Junta leads duplicados (mesma pessoa com URLs diferentes).

A busca do LinkedIn devolve a mesma pessoa ora com URL limpa, ora com
'?miniProfileUrn=...', o que criava dois leads. Este script:
  - agrupa por identificador normalizado (o slug depois de /in/)
  - mantém o lead mais antigo, move conversas/abordagens para ele
  - cancela abordagens PENDENTES duplicadas (evita abordar 2x a mesma pessoa)
  - apaga os leads repetidos e normaliza a URL do que ficou

Uso (na VM, com a .venv ativa):
    python -m scripts.limpar_duplicados
"""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.outreach import OutreachStatus, OutreachTask
from app.services.dedup import normalizar_url, url_canonica


def main() -> None:
    db = SessionLocal()
    try:
        leads = list(db.scalars(select(Lead).order_by(Lead.id)))

        grupos: dict[str, list[Lead]] = defaultdict(list)
        for lead in leads:
            chave = (lead.provider_id or "").strip() or normalizar_url(lead.linkedin_url)
            if chave:
                grupos[chave].append(lead)

        duplicados = 0
        canceladas = 0

        for chave, doGrupo in grupos.items():
            if len(doGrupo) < 2:
                continue

            principal = doGrupo[0]  # o mais antigo fica
            repetidos = doGrupo[1:]

            for rep in repetidos:
                # completa dados que faltarem no principal
                if not principal.provider_id and rep.provider_id:
                    principal.provider_id = rep.provider_id

                # move conversas
                for conv in db.scalars(
                    select(Conversation).where(Conversation.lead_id == rep.id)
                ):
                    conv.lead_id = principal.id

                # move/cancela abordagens
                for tarefa in db.scalars(
                    select(OutreachTask).where(OutreachTask.lead_id == rep.id)
                ):
                    if tarefa.status == OutreachStatus.PENDENTE:
                        tarefa.status = OutreachStatus.CANCELADO
                        tarefa.erro = "Cancelada: lead duplicado"
                        canceladas += 1
                    tarefa.lead_id = principal.id

                db.delete(rep)
                duplicados += 1

            principal.linkedin_url = (
                url_canonica(principal.linkedin_url) or principal.linkedin_url
            )

        # normaliza as URLs de todo mundo
        for lead in db.scalars(select(Lead)):
            limpa = url_canonica(lead.linkedin_url)
            if limpa and lead.linkedin_url != limpa:
                lead.linkedin_url = limpa

        db.commit()
        print(f"Leads duplicados removidos: {duplicados}")
        print(f"Abordagens pendentes canceladas (duplicadas): {canceladas}")
        print("URLs normalizadas.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
