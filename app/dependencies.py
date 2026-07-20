from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.db.database import get_session
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService


def get_conversation_service(
    session: Annotated[
        Session,
        Depends(get_session),
    ],
):

    repository = ConversationRepository(session)

    return ConversationService(repository)