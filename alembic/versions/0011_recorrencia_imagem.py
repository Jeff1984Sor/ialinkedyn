"""post.imagem_path + post_recorrencia

Revision ID: 0011_recorrencia_imagem
Revises: 0010_post
Create Date: 2026-07-18

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_recorrencia_imagem"
down_revision: str | None = "0010_post"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "post",
        sa.Column("imagem_path", sa.String(length=500), nullable=False, server_default=""),
    )
    op.create_table(
        "post_recorrencia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=160), nullable=False),
        sa.Column("tema", sa.Text(), nullable=False),
        sa.Column("frequencia", sa.String(length=20), nullable=False, server_default="SEMANAL"),
        sa.Column("dias_semana", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("hora", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("imagem_path", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("gerar_imagem_ia", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("publicar_automatico", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ultimo_criado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("post_recorrencia")
    op.drop_column("post", "imagem_path")
