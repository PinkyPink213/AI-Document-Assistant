from sqlalchemy import delete
from sqlmodel import Session, select

from app.models import ChatMessage


class ChatMessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, conversation_id: int, role: str, content: str) -> ChatMessage:
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def list_by_conversation(self, conversation_id: int) -> list[ChatMessage]:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        )
        return list(self.session.exec(statement).all())

    def delete_by_conversation_id(self, conversation_id: int) -> None:
        """Delete all persisted chat history for one conversation."""
        self.session.exec(
            delete(ChatMessage).where(
                ChatMessage.conversation_id == conversation_id
            )
        )
        self.session.commit()
