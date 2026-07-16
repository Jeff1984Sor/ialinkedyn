"""prompt_template: prompts dos agentes editaveis pelo painel

Revision ID: 0005_prompts
Revises: 0004_app_config
Create Date: 2026-07-15

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_prompts"
down_revision: str | None = "0004_app_config"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prompt_template",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chave", sa.String(length=60), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prompt_template_chave", "prompt_template", ["chave"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_prompt_template_chave", table_name="prompt_template")
    op.drop_table("prompt_template")
