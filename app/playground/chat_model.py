from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.ai.chat_model import get_chat_model

llm = get_chat_model()

response = llm.invoke(
    [
        SystemMessage(content="You are a Python teacher."),
        HumanMessage(content="Explain FastAPI"),
    ]
    )

print(response.content)

# uv run python -m app.playground.chat_model