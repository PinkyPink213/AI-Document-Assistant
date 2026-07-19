from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()

chat_service = ChatService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint to handle chat requests.
    """
    answer = chat_service.chat(request.message)
    
    print("Type:",type(request))
    print(request)
    print( request.model_dump())
    return ChatResponse(answer=answer)
