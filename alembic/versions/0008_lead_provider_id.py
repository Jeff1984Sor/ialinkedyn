"""lead.provider_id: id interno da pessoa no provedor

Revision ID: 0008_lead_provider_id
Revises: 0007_campanha
Create Date: 2026-07-18

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_lead_provider_id"
down_revision: str | None = "0007_campanha"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lead",
        sa.Column("provider_id", sa.String(length=200), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("lead", "provider_id")
