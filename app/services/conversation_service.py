from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationUpdate
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository 
class ConversationService:
    def __init__(self,repository: ConversationRepository):
        self.repository = repository
    
    def create(self, request: ConversationCreate) -> ConversationResponse:
        """
        Create a new conversation and return the response.
        """
        conversation = Conversation(title=request.title)
        return self.respository.create(conversation)
    
    def get_all(self):

        return self.respository.get_all()
    
    def get_by_id(self,conversation_id: int)->ConversationResponse:
        """
        Retrieve a conversation by its ID.
        """
        conversation = self.repository.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError("Conversation not found")
        return conversation
    
    def update(self, conversation_id: int, request: ConversationUpdate) -> ConversationResponse:
        """
        Update an existing conversation and return the updated response.
        """
        conversation = self.respository.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError("Conversation not found")
        conversation.title = request.title
        return self.repository.update(conversation)    
    
    def delete(self, conversation_id: int) -> ConversationResponse:
        """
        Delete a conversation by its ID and return the deleted response.
        """
        conversation = self.repository.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError("Conversation not found")
        self.repository.delete(conversation)        