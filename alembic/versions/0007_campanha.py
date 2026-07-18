"""campanha: audience (publico-alvo) + outreach_task (fila de abordagens)

Revision ID: 0007_campanha
Revises: 0006_unipile_account
Create Date: 2026-07-18

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_campanha"
down_revision: str | None = "0006_unipile_account"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audience",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("termo", sa.Text(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False, server_default=""),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "outreach_task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audience_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="CONVITE"),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDENTE"),
        sa.Column("erro", sa.Text(), nullable=False, server_default=""),
        sa.Column("enviado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_outreach_task_lead_id", "outreach_task", ["lead_id"])
    op.create_index("ix_outreach_task_status", "outreach_task", ["status"])


def downgrade() -> None:
    op.drop_index("ix_outreach_task_status", table_name="outreach_task")
    op.drop_index("ix_outreach_task_lead_id", table_name="outreach_task")
    op.drop_table("outreach_task")
    op.drop_table("audience")
