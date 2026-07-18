"""post: conteudo do feed (rascunho, agendado, publicado)

Revision ID: 0010_post
Revises: 0009_seguir_automatico
Create Date: 2026-07-18

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_post"
down_revision: str | None = "0009_seguir_automatico"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "post",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("tema", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="RASCUNHO"),
        sa.Column("agendado_para", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publicado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_id", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("erro", sa.Text(), nullable=False, server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_post_status", "post", ["status"])


def downgrade() -> None:
    op.drop_index("ix_post_status", table_name="post")
    op.drop_table("post")
