"""Add language field to users table

Revision ID: 001
Revises:
Create Date: 2026-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("language", sa.String(5), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("users", "language")
