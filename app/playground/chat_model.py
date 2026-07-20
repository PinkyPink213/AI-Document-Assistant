from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.ai.chat_model import get_chat_model

llm = get_chat_model()

response = llm.invoke(
    [
        HumanMessage(content="Hello, how are you?")
    ]
    )

print(response.content)

# uv run python -m app.playground.chat_model