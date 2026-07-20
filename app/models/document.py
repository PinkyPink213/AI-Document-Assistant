from datetime import UTC, datetime
from sqlmodel import Field, SQLModel

class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)

    conversation_id: int = Field(foreign_key="conversations.id")

    filename: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))