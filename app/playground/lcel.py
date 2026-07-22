from app.ai.chat_model import get_chat_model
from app.ai.prompts import RAG_PROMPT

llm = get_chat_model()

chain = RAG_PROMPT | llm

response = chain.invoke(
    {
        "context": "",
        "question": "What is FastAPI?"
    }
)

print(response.content)
#  uv run python -m app.playground.lcel 