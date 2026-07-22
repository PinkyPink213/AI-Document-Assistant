from app.schemas import ConversationCreate, ConversationResponse, ConversationUpdate
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository 
from fastapi import HTTPException
class ConversationService:
    def __init__(self,repository: ConversationRepository):
        self.repository = repository
    
    def create(self, request: ConversationCreate) -> ConversationResponse:
        """
        Create a new conversation and return the response.
        """
        conversation = Conversation(title=request.title)
        conversation = self.repository.create(conversation)
        return ConversationResponse.model_validate(conversation)
    
    def get_all(self) -> list[ConversationResponse]:

        conversations = self.repository.get_all()

        return [
            ConversationResponse.model_validate(conversation)
            for conversation in conversations
        ]
    
    def get_by_id(self,conversation_id: int)->ConversationResponse:
        """
        Retrieve a conversation by its ID.
        """
        conversation = self.repository.get_by_id(conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        return ConversationResponse.model_validate(conversation)
    
    def update(self, conversation_id: int, request: ConversationUpdate) -> ConversationResponse:
        """
        Update an existing conversation and return the updated response.
        """
        conversation = self.repository.get_by_id(conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        conversation.title = request.title

        conversation = self.repository.update(conversation)

        return ConversationResponse.model_validate(conversation)  
    
    def delete(self, conversation_id: int) -> ConversationResponse:
        """
        Delete a conversation by its ID and return the deleted response.
        """
        conversation = self.repository.get_by_id(conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        self.repository.delete(conversation)     