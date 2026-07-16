"""app_config: configuracao da ferramenta pelo painel (chaves cifradas)

Revision ID: 0004_app_config
Revises: 0003_conexao
Create Date: 2026-07-15

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_app_config"
down_revision: str | None = "0003_conexao"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("linkedin_provider", sa.String(length=40), nullable=False, server_default="mock"),
        sa.Column("unipile_dsn", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("unipile_api_key_cifrado", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("gemini_api_key_cifrado", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("gemini_model", sa.String(length=80), nullable=False, server_default="gemini-2.5-flash"),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_config")
