from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationUpdate
from app.db import fake_db

class ConversationService:
    
    def create(self, request: ConversationCreate) -> ConversationResponse:
        """
        Create a new conversation and return the response.
        """
        # Simulate saving to a database by appending to the fake_db list
        conversation = ConversationResponse(id=len(fake_db) + 1, title=request.title)
        fake_db.append(conversation)
        return conversation
    
    def get_all(self):

        return fake_db
    
    def get_by_id(self,conversation_id: int)->ConversationResponse:
        """
        Retrieve a conversation by its ID.
        """
        for conversation in fake_db:
            if conversation.id == conversation_id:
                return conversation
        return ValueError("Conversation not found")
    
    def update(self, conversation_id: int, request: ConversationUpdate) -> ConversationResponse:
        """
        Update an existing conversation and return the updated response.
        """
        for conversation in fake_db:
            if conversation.id == conversation_id:
                conversation.title = request.title
                return conversation
        return ValueError("Conversation not found")
    
    def delete(self, conversation_id: int) -> ConversationResponse:
        """
        Delete a conversation by its ID and return the deleted response.
        """
        for i, conversation in enumerate(fake_db):
            if conversation.id == conversation_id:
                deleted_conversation = fake_db.pop(i)
                return deleted_conversation
        return ValueError("Conversation not found")