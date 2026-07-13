"""Cria (ou atualiza a senha de) um usuário de login.

Uso (na VM, com a .venv ativa):
    python -m scripts.criar_admin <email> <nome> <senha>

Ex.:
    python -m scripts.criar_admin mayacorp22@gmail.com "Jefferson" "minhaSenhaForte"
"""
from __future__ import annotations

import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def main() -> None:
    if len(sys.argv) != 4:
        print("Uso: python -m scripts.criar_admin <email> <nome> <senha>")
        raise SystemExit(1)

    email, nome, senha = sys.argv[1], sys.argv[2], sys.argv[3]

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.senha_hash = hash_password(senha)
            user.nome = nome
            user.ativo = True
            acao = "atualizado"
        else:
            user = User(email=email, nome=nome, senha_hash=hash_password(senha))
            db.add(user)
            acao = "criado"
        db.commit()
        db.refresh(user)
        print(f"Usuário {acao}: id={user.id} email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
