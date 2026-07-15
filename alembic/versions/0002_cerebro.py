"""cerebro: knowledge_item, brand_voice, lead, conversation, message

Revision ID: 0002_cerebro
Revises: 0001_initial
Create Date: 2026-07-15

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_cerebro"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pergunta", sa.Text(), nullable=False),
        sa.Column("resposta", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("categoria", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "brand_voice",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome_assistente", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("persona", sa.Text(), nullable=False, server_default=""),
        sa.Column("avatar_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("assina_mensagens", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("descricao_empresa", sa.Text(), nullable=False, server_default=""),
        sa.Column("tom", sa.Text(), nullable=False, server_default=""),
        sa.Column("icp", sa.Text(), nullable=False, server_default=""),
        sa.Column("cta", sa.Text(), nullable=False, server_default=""),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "lead",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=180), nullable=False),
        sa.Column("headline", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("empresa", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("cargo", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("origem", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="NOVO"),
        sa.Column("notas", sa.Text(), nullable=False, server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "conversation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canal", sa.String(length=60), nullable=False, server_default="linkedin"),
        sa.Column("external_id", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_conversation_lead_id", "conversation", ["lead_id"])

    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False),
        sa.Column("autor", sa.String(length=20), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_message_conversation_id", "message", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_message_conversation_id", table_name="message")
    op.drop_table("message")
    op.drop_index("ix_conversation_lead_id", table_name="conversation")
    op.drop_table("conversation")
    op.drop_table("lead")
    op.drop_table("brand_voice")
    op.drop_table("knowledge_item")
