"""Dependencies compartilhadas do FastAPI (auth, sessão de banco).

Single-tenant: não há tenant_id. Apenas identifica o usuário logado.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decodificar_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Valida o JWT e carrega o usuário correspondente do banco."""
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = decodificar_token(token)
    if sub is None:
        raise credenciais_invalidas
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credenciais_invalidas

    user = db.get(User, user_id)
    if user is None or not user.ativo:
        raise credenciais_invalidas
    return user


__all__ = ["get_db", "get_current_user", "oauth2_scheme", "Session"]
