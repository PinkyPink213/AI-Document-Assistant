from sqlmodel import Session, select

from app.models.conversation import Conversation


class ConversationRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, conversation: Conversation) -> Conversation:

        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)

        return conversation

    def get_all(self) -> list[Conversation]:

        statement = select(Conversation)

        return self.session.exec(statement).all()

    def get_by_id(self, conversation_id: int) -> Conversation | None:

        return self.session.get(Conversation, conversation_id)

    def update(self, conversation: Conversation) -> Conversation:

        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)

        return conversation

    def delete(self, conversation: Conversation):

        self.session.delete(conversation)
        self.session.commit()