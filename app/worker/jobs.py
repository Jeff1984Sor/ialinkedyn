"""Jobs do worker."""
from __future__ import annotations

import logging
import random

from app.core.database import SessionLocal
from app.services.growth import detectar_aceites
from app.services.outreach import processar_fila

log = logging.getLogger("ialinkedyn.worker")


def job_enviar_abordagens() -> None:
    """Envia no máximo UMA abordagem por execução, e ainda pula algumas rodadas
    de propósito — assim o envio não fica com cara de robô (intervalo irregular).
    """
    # ~60% das rodadas não fazem nada: cria intervalos aleatórios entre envios
    if random.random() < 0.6:
        return

    db = SessionLocal()
    try:
        resultado = processar_fila(db, maximo=1)
        if resultado["enviados"]:
            log.info("Abordagem enviada (%s)", resultado["motivo"])
        elif resultado["motivo"] not in ("fila vazia",):
            log.info("Nada enviado: %s", resultado["motivo"])
    except Exception:  # pragma: no cover
        log.exception("Falha ao processar a fila de abordagens")
    finally:
        db.close()


def job_detectar_aceites() -> None:
    """Vê quem aceitou o convite e já enfileira a 1ª mensagem no chat."""
    db = SessionLocal()
    try:
        r = detectar_aceites(db)
        if r["aceites"]:
            log.info(
                "Aceites detectados: %s | follow-ups enfileirados: %s",
                r["aceites"],
                r["followups"],
            )
    except Exception:  # pragma: no cover
        log.exception("Falha ao detectar aceites")
    finally:
        db.close()
