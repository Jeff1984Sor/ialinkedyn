"""app_config: unipile_account_id + escolha de IA (gemini/openai)

Revision ID: 0006_unipile_account
Revises: 0005_prompts
Create Date: 2026-07-18

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_unipile_account"
down_revision: str | None = "0005_prompts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("unipile_account_id", sa.String(length=120), nullable=False, server_default=""),
    )
    op.add_column(
        "app_config",
        sa.Column("ia_provider", sa.String(length=20), nullable=False, server_default="gemini"),
    )
    op.add_column(
        "app_config",
        sa.Column("openai_api_key_cifrado", sa.String(length=1000), nullable=False, server_default=""),
    )
    op.add_column(
        "app_config",
        sa.Column("openai_model", sa.String(length=80), nullable=False, server_default="gpt-4o"),
    )


def downgrade() -> None:
    op.drop_column("app_config", "openai_model")
    op.drop_column("app_config", "openai_api_key_cifrado")
    op.drop_column("app_config", "ia_provider")
    op.drop_column("app_config", "unipile_account_id")
