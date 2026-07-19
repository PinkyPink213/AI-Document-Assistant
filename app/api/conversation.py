from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

from app.db.database import get_session
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationCreate,ConversationResponse,ConversationUpdate

from app.services.conversation_service import ConversationService
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.services.conversation_service import ConversationService
from typing import List

router = APIRouter()
def get_conversation_service(session: Annotated[Session,Depends(get_session),]):

    repository = ConversationRepository(session)

    return ConversationService(repository)


@router.post("/conversation",response_model=ConversationResponse,)
def create_conversation(request: ConversationCreate, service: Annotated[ConversationService,Depends(get_conversation_service), ],):

    return service.create(request)


@router.get( "/conversation",response_model=list[ConversationResponse])
def get_all(service: Annotated[ConversationService,Depends(get_conversation_service)]):

    return service.get_all()


@router.get("/conversation/{conversation_id}",response_model=ConversationResponse,)
def get_by_id(
    conversation_id: int,
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
):
    try:
        return service.get_by_id(conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e),)


@router.put("/conversation/{conversation_id}",response_model=ConversationResponse,)
def update(
    conversation_id: int,
    request: ConversationUpdate,
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
):

    try:
        return service.update(conversation_id,request,)
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e),)


@router.delete("/conversation/{conversation_id}",status_code=204,)
def delete(
    conversation_id: int,
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
):
    try:
        service.delete(conversation_id)
        return Response(status_code=204)
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e),)