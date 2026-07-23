from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):

    __tablename__ = "documents"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    conversation_id: int = Field(
        foreign_key="conversations.id",
    )

    filename: str
    chunk_count: int = Field(default=0)
    vector_document_id: str = Field(default_factory=lambda: str(uuid4()), index=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
