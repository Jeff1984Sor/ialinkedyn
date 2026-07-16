"""conexao: linkedin_account + automation_settings

Revision ID: 0003_conexao
Revises: 0002_cerebro
Create Date: 2026-07-15

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_conexao"
down_revision: str | None = "0002_cerebro"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "linkedin_account",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="mock"),
        sa.Column("external_account_id", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DESCONECTADO"),
        sa.Column("token_cifrado", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("conectado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "automation_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("limite_follows_dia", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("limite_convites_dia", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("limite_mensagens_dia", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("modo_chat", sa.String(length=10), nullable=False, server_default="MANUAL"),
        sa.Column("horario_inicio", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("horario_fim", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("automation_settings")
    op.drop_table("linkedin_account")
