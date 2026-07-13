"""inicial: tabela user

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-13

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario", sa.String(length=60), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_user_usuario", "user", ["usuario"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_usuario", table_name="user")
    op.drop_table("user")
