from typing import Annotated

from fastapi import Depends
from sqlmodel import Session
from pathlib import Path
from app.db.database import engine
from app.db.database import get_session
from app.repositories import ChatMessageRepository, DocumentRepository, ConversationRepository
from app.services import ConversationService, AgentService, IndexService, DocumentService
from app.ai import (
    get_vectorstore,
    get_qdrant_client,
    get_embeddings
)
def get_conversation_service(
    session: Annotated[
        Session,
        Depends(get_session),
    ],
):

    repository = ConversationRepository(session)

    return ConversationService(repository)

def get_agent_service(
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> AgentService:
    return AgentService(ChatMessageRepository(session))

def get_document_service(
    session: Annotated[
        Session,
        Depends(get_session),
    ],
):
    repository = DocumentRepository(session)

    client = get_qdrant_client()
    embeddings = get_embeddings()
    vector_store = get_vectorstore(client, embeddings)

    index_service = IndexService(vector_store)

    return DocumentService(repository, index_service)

def get_index_service() -> IndexService:
    client = get_qdrant_client()
    embeddings = get_embeddings()
    vector_store = get_vectorstore(client, embeddings)
    return  IndexService(vector_store)

DocumentServiceDep = Annotated[
    DocumentService,
    Depends(get_document_service)
]
