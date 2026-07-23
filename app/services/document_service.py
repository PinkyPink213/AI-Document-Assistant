from pathlib import Path
from sqlmodel import Session
from app.db.database import engine
from app.repositories import DocumentRepository
from app.services import IndexService
from app.models import Document
from uuid import uuid4


class DocumentAlreadyExistsError(ValueError):
    pass


class DocumentService:
    """
    Service responsible for managing document metadata
    and vector indexing.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        index_service: IndexService,
    ):
        self.repository = repository
        self.index_service = index_service

    async def upload_document(
        self,
        conversation_id: int,
        pdf_bytes: bytes,
        filename: str,
    ):
        existing = self.repository.get_by_conversation_and_filename(
            conversation_id,
            filename,
        )
        if existing:
            raise DocumentAlreadyExistsError(
                f"'{filename}' is already uploaded in this conversation."
            )

        vector_document_id = str(uuid4())
        chunk_count = await self.index_service.index_pdf(
            conversation_id,
            pdf_bytes,
            filename,
            vector_document_id,
        )

        document = Document(
            conversation_id=conversation_id,
            filename=filename,
            chunk_count=chunk_count,
            vector_document_id=vector_document_id,
        )

        return self.repository.create(document)

    def list_documents(self):
        return self.repository.get_all()

    def get_document(
        self,
        document_id: int,
    ):
        return self.repository.get_by_id(document_id)

    def delete_document(
        self,
        document_id: int,
    ) -> bool:
        document = self.repository.get_by_id(document_id)

        if document is None:
            return False

        # Delete vectors from Qdrant
        self.index_service.delete_document(document.vector_document_id)

        # Delete metadata from PostgreSQL
        self.repository.delete(document)

        return True

    def list_documents(
        self,
        conversation_id: int,
    ):
        return self.repository.get_by_conversation_id(conversation_id)
