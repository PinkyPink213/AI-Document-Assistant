from langchain.chat_models import init_chat_model

from app.core.config  import settings

def get_llm():
    return init_chat_model(
        model=settings.openai_chat_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
