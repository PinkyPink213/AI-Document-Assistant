"""add document chunk count

Revision ID: f2a4d9c73b10
Revises: ce1fcfda8bfd
Create Date: 2026-07-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f2a4d9c73b10"
down_revision: Union[str, Sequence[str], None] = "ce1fcfda8bfd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("documents", "chunk_count")
