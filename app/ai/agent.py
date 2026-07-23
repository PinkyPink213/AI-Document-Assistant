from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.core.config import settings
from app.ai import (
    list_uploaded_documents,
    count_uploaded_documents,
    count_pdf_pages,
    search_documents,
    search_academic_papers,
    delete_document,
    build_agent_prompt,
    get_human_in_the_loop,
)


def get_tools():
    return [
        list_uploaded_documents,
        count_uploaded_documents,
        count_pdf_pages,
        search_documents,
        search_academic_papers,
        delete_document,
    ]


def get_model():

    return init_chat_model(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


def build_agent(checkpointer: BaseCheckpointSaver):
    return create_agent(
        model=get_model(),
        tools=get_tools(),
        system_prompt=build_agent_prompt(),
        middleware=[
            get_human_in_the_loop()
        ],
        checkpointer=checkpointer,
        name="pdf_assistant",
    )
