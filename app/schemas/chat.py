from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: int = Field(
        ...,
        description="Conversation ID",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="User message",
    )


class ResumeRequest(BaseModel):
    conversation_id: int = Field(
        ...,
        description="Conversation ID",
    )
    decision: Literal["approve", "reject"] = Field(
        ...,
        description="Human approval decision",
    )
    message: str | None = Field(
        default=None,
        description="Optional feedback message",
    )


class ChatResponse(BaseModel):
    response: str | None = Field(
        default=None,
        description="Assistant response",
    )
    interrupt: dict[str, Any] | None = Field(
        default=None,
        description="Human-in-the-loop interrupt payload",
    )


class ChatMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
