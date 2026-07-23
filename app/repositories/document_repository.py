from sqlalchemy import delete, func
from sqlmodel import Session, select
from app.models import Document


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, document: Document) -> Document:
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document
    
    def get_all(self) -> list[Document]:

        statement = select(Document)

        return self.session.exec(statement).all()

    def get_by_id(self, document_id: int) -> Document | None:

        return self.session.get(Document, document_id)

    def update(self, document: Document) -> Document:

        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)

        return document

    def delete(self, document: Document):

        self.session.delete(document)
        self.session.commit()
        
    def get_by_conversation_id(self, conversation_id: int,):
        statement = (
            select(Document)
            .where(Document.conversation_id == conversation_id)
        )

        return self.session.exec(statement).all()

    def get_by_conversation_and_filename(
        self,
        conversation_id: int,
        filename: str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.conversation_id == conversation_id,
            func.lower(Document.filename) == filename.strip().lower(),
        )
        return self.session.exec(statement).first()

    def delete_by_conversation_id(self, conversation_id: int) -> None:
        self.session.exec(
            delete(Document).where(Document.conversation_id == conversation_id)
        )
