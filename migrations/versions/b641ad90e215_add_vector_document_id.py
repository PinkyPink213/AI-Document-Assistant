"""add vector document id

Revision ID: b641ad90e215
Revises: f2a4d9c73b10
Create Date: 2026-07-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b641ad90e215"
down_revision: Union[str, Sequence[str], None] = "f2a4d9c73b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("vector_document_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_documents_vector_document_id",
        "documents",
        ["vector_document_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_vector_document_id", table_name="documents")
    op.drop_column("documents", "vector_document_id")
