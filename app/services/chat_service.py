class ChatService:

    def chat(self, message: str) -> str:
        prompt = f"""
You are a helpful AI assistant.

User:
{message}
"""

        return prompt
    
    