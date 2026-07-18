"""Segurança: hashing de senha (bcrypt), JWT e criptografia Fernet.

- Senhas dos usuários: bcrypt (passlib).
- Tokens JWT de login: python-jose.
- Tokens de terceiros (ex. Unipile/LinkedIn): criptografados com Fernet
  antes de ir pro banco.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# --- Senhas ---
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(senha: str) -> str:
    return _pwd_context.hash(senha)


def verify_password(senha: str, senha_hash: str) -> bool:
    return _pwd_context.verify(senha, senha_hash)


# --- JWT ---
def criar_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """Gera um JWT cujo 'sub' é o id/identificador do usuário."""
    minutes = expires_minutes or settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> str | None:
    """Devolve o 'sub' do token, ou None se inválido/expirado."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None


# --- Fernet (tokens de terceiros) ---
_ERRO_FERNET = (
    "FERNET_KEY inválida ou ausente no .env do servidor. Ela precisa ser uma chave "
    "base64 de 32 bytes. Gere com: "
    'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" '
    "e coloque em FERNET_KEY no .env, depois reinicie a API."
)


def _fernet() -> Fernet:
    if not settings.fernet_key:
        raise HTTPException(status_code=500, detail=_ERRO_FERNET)
    try:
        return Fernet(settings.fernet_key.encode())
    except (ValueError, TypeError):
        raise HTTPException(status_code=500, detail=_ERRO_FERNET)


def encrypt_token(valor: str) -> str:
    """Criptografa um segredo (ex. token do provedor) para salvar no banco."""
    return _fernet().encrypt(valor.encode()).decode()


def decrypt_token(valor_cifrado: str) -> str:
    """Descriptografa um segredo lido do banco."""
    return _fernet().decrypt(valor_cifrado.encode()).decode()
