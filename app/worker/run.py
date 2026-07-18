"""Worker do IALinkedyn (APScheduler).

Roda em processo separado da API:
    python -m app.worker.run
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.worker.jobs import (
    job_detectar_aceites,
    job_enviar_abordagens,
    job_publicar_posts,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("ialinkedyn.worker")


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")

    # a cada 2 minutos o job "acorda"; ele mesmo sorteia se envia ou não,
    # e o serviço respeita horário de trabalho e limite diário.
    scheduler.add_job(
        job_enviar_abordagens,
        "interval",
        minutes=2,
        id="enviar_abordagens",
        max_instances=1,
        coalesce=True,
    )

    # a cada 15 min verifica quem aceitou o convite e enfileira o follow-up
    scheduler.add_job(
        job_detectar_aceites,
        "interval",
        minutes=15,
        id="detectar_aceites",
        max_instances=1,
        coalesce=True,
    )

    # a cada minuto verifica se algum post agendado venceu
    scheduler.add_job(
        job_publicar_posts,
        "interval",
        minutes=1,
        id="publicar_posts",
        max_instances=1,
        coalesce=True,
    )

    log.info(
        "Worker iniciado. Jobs: enviar_abordagens (2 min), "
        "detectar_aceites (15 min), publicar_posts (1 min)."
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover
        log.info("Worker encerrado.")


if __name__ == "__main__":
    main()
