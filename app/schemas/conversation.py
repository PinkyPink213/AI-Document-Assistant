from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

class ConversationCreate(BaseModel):

    title: str = Field(
        min_length=3,
        max_length=100,
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:

        if value.lower() == "admin":
            raise ValueError(
                "Title cannot be admin."
            )

        return value


class ConversationUpdate(BaseModel):

    title: str = Field(
        min_length=3,
        max_length=100,
    )




class ConversationResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    title: str
    created_at: datetime