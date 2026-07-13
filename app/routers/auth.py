"""Rotas de autenticação: registrar, login e dados do usuário logado."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import criar_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(dados: UserCreate, db: Session = Depends(get_db)) -> User:
    """Cria um usuário. Single-tenant: uso interno (poucos usuários)."""
    existe = db.scalar(select(User).where(User.usuario == dados.usuario))
    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com esse login",
        )
    user = User(
        usuario=dados.usuario,
        nome=dados.nome,
        senha_hash=hash_password(dados.senha),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Login via formulário OAuth2 (username = usuário)."""
    user = db.scalar(select(User).where(User.usuario == form.username))
    if not user or not verify_password(form.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")
    token = criar_access_token(user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)) -> User:
    """Devolve o usuário autenticado."""
    return current
