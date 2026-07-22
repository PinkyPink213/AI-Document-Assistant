
from langchain_openai import OpenAIEmbeddings
from app.core.config  import settings

def get_embeddings()->OpenAIEmbeddings:
    """
    Returns an instance of OpenAIEmbeddings with the specified model and API key.
    """
    embeddings = OpenAIEmbeddings(
        model=settings.openai_embeddings_model,
        api_key=settings.openai_api_key,
    )
    return embeddings