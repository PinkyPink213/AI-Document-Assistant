from langchain.chat_models import init_chat_model

from app.core.config import settings


def get_chat_model():
    return init_chat_model(
        model="openai:gpt-4.1-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
    )