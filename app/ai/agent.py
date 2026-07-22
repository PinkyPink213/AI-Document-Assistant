from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


from app.core.config  import settings
from app.ai import (
    list_uploaded_documents,
    count_pdf_pages,
    search_documents,
    delete_document,
    build_agent_prompt,
    get_human_in_the_loop,
    get_mcp_tools
)


# from langgraph.checkpoint.postgres import PostgresSaver

# checkpointer = PostgresSaver.from_conn_string(
#     settings.postgres_url
# )
# checkpointer.setup()

THREAD_CONFIG = {
    "configurable": {
        "thread_id": "demo-thread",
    }
}

def get_tools():

    return [
        list_uploaded_documents,
        count_pdf_pages,
        search_documents,
        delete_document,
        get_mcp_tools
        
    ]


def get_model():

    return init_chat_model(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


def build_agent():

    return create_agent(
        model=get_model(),
        tools=get_tools(),
        system_prompt=build_agent_prompt(),
        middleware=[
            get_human_in_the_loop()
        ],
        checkpointer=InMemorySaver(),
        name="pdf_assistant",
    )
    
agent = build_agent()
