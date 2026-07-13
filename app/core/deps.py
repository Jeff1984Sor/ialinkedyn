"""Dependencies compartilhadas do FastAPI (auth, sessão de banco).

Single-tenant: não há tenant_id. Apenas identifica o usuário logado.
O model User entra na Etapa 2 (auth). Por ora, get_current_user já deixa
o esqueleto pronto e será ligado ao User quando ele existir.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decodificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Extrai e valida o id do usuário a partir do JWT.

    Etapa 2 vai evoluir para carregar o objeto User do banco.
    """
    sub = decodificar_token(token)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado",
        )


# Reexport para conveniência
__all__ = ["get_db", "get_current_user_id", "oauth2_scheme", "Session"]
