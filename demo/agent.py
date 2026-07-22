from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
import os


from app.core.config  import settings
from demo.tools import (
    list_uploaded_documents,
    count_pdf_pages,
    search_documents,
    delete_document
)


SYSTEM_PROMPT = """
You are a helpful PDF assistant.

Guidelines:
- Use tools whenever document information is required.
- Never guess filenames or page counts.
- If a tool returns no data, explain it politely.
"""

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
        delete_document
    ]


def get_model():

    return init_chat_model(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


def build_agent():
    checkpointer = InMemorySaver()

    return create_agent(
        model=get_model(),
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
        name="pdf_assistant",
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "delete_document": {
                        "allowed_decisions": [
                            "approve",
                            "reject",
                        ]
                    }
                }
            )
        ],

        checkpointer=checkpointer,
    )


agent = build_agent()


def chat(question: str):

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        config=THREAD_CONFIG,
        version="v2",
    )

    if result.interrupts:
        return result

    return result.value["messages"][-1].content


def handle_interrupt(result):

    interrupt = result.interrupts[0].value

    action = interrupt["action_requests"][0]

    print("=" * 60)
    print(" HUMAN APPROVAL REQUIRED")
    print("=" * 60)
    print()
    print("The assistant wants to perform the following action.\n")

    print("Tool")
    print(f"  {action['name']}\n")

    print("Arguments")

    for key, value in action["args"].items():
        print(f"  {key:<12}: {value}")

    print()
    print("-" * 60)

    while True:

        choice = input(
            "Approve this action? [y/N]: "
        ).strip().lower()

        if choice in ("y", "yes"):

            decision = {
                "type": "approve"
            }
            break

        if choice in ("n", "no", ""):

            decision = {
                "type": "reject",
                "message": "Operation cancelled by user."
            }
            break

        print("Please enter 'y' or 'n'.")

    response = agent.invoke(
        Command(
            resume={
                "decisions": [
                    decision
                ]
            }
        ),
        config=THREAD_CONFIG,
        version="v2",
    )

    return response.value["messages"][-1].content

def main():

    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_TRACING"] = settings.langsmith_tracing

    print("Answer 1: ",chat("How many pages does attention.pdf have?"))

    print("Answer 2: ",chat( "List all uploaded PDF files." ))
    
    # print("Answer 3: ", chat( "What is Transformer" ))
    
    # result = chat("Delete attention.pdf")

    # if result.interrupts:

    #     print(handle_interrupt(result))

    # else:

    #     print(result.value["messages"][-1].content)


if __name__ == "__main__":
    main()