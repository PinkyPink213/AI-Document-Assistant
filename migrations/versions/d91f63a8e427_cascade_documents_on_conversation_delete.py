"""cascade documents on conversation delete

Revision ID: d91f63a8e427
Revises: c824ef61a930
Create Date: 2026-07-24
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d91f63a8e427"
down_revision: Union[str, Sequence[str], None] = "c824ef61a930"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "documents_conversation_id_fkey",
        "documents",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "documents_conversation_id_fkey",
        "documents",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "documents_conversation_id_fkey",
        "documents",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "documents_conversation_id_fkey",
        "documents",
        "conversations",
        ["conversation_id"],
        ["id"],
    )
