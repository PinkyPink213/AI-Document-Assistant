import os
from app.core.config  import settings

def configure_langsmith() -> None:
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
