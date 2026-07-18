"""automation_settings.seguir_automatico

Revision ID: 0009_seguir_automatico
Revises: 0008_lead_provider_id
Create Date: 2026-07-18

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_seguir_automatico"
down_revision: str | None = "0008_lead_provider_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "automation_settings",
        sa.Column("seguir_automatico", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("automation_settings", "seguir_automatico")
