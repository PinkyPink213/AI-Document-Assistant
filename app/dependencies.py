from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from app.db.database import get_session
from app.repositories import (
    ChatMessageRepository,
    ConversationRepository,
    DocumentRepository,
)
from app.services import AgentService, ConversationService, DocumentService, IndexService
from app.ai import (
    get_vectorstore,
    get_qdrant_client,
    get_embeddings
)


def get_conversation_service(
    request: Request,
    session: Annotated[
        Session,
        Depends(get_session),
    ],
):

    return ConversationService(
        ConversationRepository(session),
        DocumentRepository(session),
        ChatMessageRepository(session),
        get_qdrant_client(),
        request.app.state.agent.checkpointer,
    )

def get_agent_service(
    request: Request,
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> AgentService:
    return AgentService(
        ChatMessageRepository(session),
        request.app.state.agent,
        request.app.state.delete_document_workflow,
        ConversationRepository(session),
    )

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
