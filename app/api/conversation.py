from fastapi import APIRouter,Response
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.services.conversation_service import ConversationService
from typing import List

router = APIRouter()
service = ConversationService()

@router.post("/conversation", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreate):
    """
    Endpoint to handle conversation requests.
    """
    return service.create(request)

@router.get("/conversation", response_model=List[ConversationResponse])
async def get_conversations():
    """
    Endpoint to retrieve all conversations.
    """
    return service.get_all()

@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    """
    Endpoint to retrieve a conversation by its ID.
    """
    return service.get_by_id(conversation_id)

@router.put("/conversation/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: int, request: ConversationCreate):
    """
    Endpoint to update a conversation by its ID.
    """
    return service.update(conversation_id, request)

@router.delete("/conversation/{conversation_id}", response_model=ConversationResponse)
async def delete_conversation(conversation_id: int):
    """
    Endpoint to delete a conversation by its ID.
    """
    service.delete(conversation_id)
    return Response(status_code=204, content=None)