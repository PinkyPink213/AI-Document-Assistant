from app.schemas import ConversationCreate, ConversationResponse, ConversationUpdate
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository 
from app.repositories.document_repository import DocumentRepository
from app.core.config.settings import settings
from fastapi import HTTPException
from qdrant_client.models import FieldCondition, Filter, MatchValue

class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
        document_repository: DocumentRepository,
        qdrant_client,
    ):
        self.repository = repository
        self.document_repository = document_repository
        self.qdrant_client = qdrant_client
    
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

        self.qdrant_client.delete(
            collection_name=settings.qdrant_collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.conversation_id",
                        match=MatchValue(value=conversation_id),
                    )
                ]
            ),
            wait=True,
        )
        self.document_repository.delete_by_conversation_id(conversation_id)
        self.repository.delete(conversation)
