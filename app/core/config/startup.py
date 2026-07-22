from .langsmith import configure_langsmith
from .logging_config import setup_logging

from app.ai import initialize_vectorstore,get_qdrant_client


def startup():
    client=get_qdrant_client()
    setup_logging()
    configure_langsmith()
    initialize_vectorstore(client)