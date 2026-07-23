import logging
import re

from langgraph.types import Command

from app.ai.agent import agent
from app.repositories import ChatMessageRepository

logger = logging.getLogger(__name__)


SOURCE_PATTERN = re.compile(
    r"\[SOURCE \d+:\s*([^,\]]+),\s*page\s*([^\]]+)\]",
    re.IGNORECASE,
)
ACADEMIC_SOURCE_PATTERN = re.compile(
    r"\[ACADEMIC SOURCE \d+:\s*(.*?)\s*\|\s*(https?://[^\]\s]+)\]",
    re.IGNORECASE,
)


def get_pending_interrupt(state) -> dict | None:
    for task in getattr(state, "tasks", ()):
        for interrupt in getattr(task, "interrupts", ()):
            value = getattr(interrupt, "value", None)
            if isinstance(value, dict):
                return value
    return None


def ensure_source_citations(response: str, messages: list) -> str:
    sources: list[tuple[str, str]] = []
    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue
        content = str(getattr(message, "content", ""))
        for filename, page in SOURCE_PATTERN.findall(content):
            source = (filename.strip(), page.strip())
            if source not in sources:
                sources.append(source)

    if not sources or re.search(r"\[[^\]]+,\s*p\.\s*[^\]]+\]", response):
        return response

    source_list = "\n".join(
        f"- [{filename}, p. {page}]" for filename, page in sources
    )
    return f"{response.rstrip()}\n\n**Sources**\n{source_list}"


def ensure_academic_citations(response: str, messages: list) -> str:
    sources: list[tuple[str, str]] = []
    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue
        content = str(getattr(message, "content", ""))
        for title, url in ACADEMIC_SOURCE_PATTERN.findall(content):
            source = (title.strip(), url.strip())
            if source not in sources:
                sources.append(source)

    if not sources or any(url in response for _, url in sources):
        return response

    source_list = "\n".join(f"- [{title}]({url})" for title, url in sources)
    return f"{response.rstrip()}\n\n**Academic sources**\n{source_list}"


class AgentService:
    """
    Service responsible for interacting with the LangGraph Agent.
    """

    def __init__(self, message_repository: ChatMessageRepository):
        self.agent = agent
        self.message_repository = message_repository

    def list_messages(self, conversation_id: int):
        return self.message_repository.list_by_conversation(conversation_id)

    async def chat(
        self,
        conversation_id: int,
        question: str, 
    ):
        """
        Send a user message to the agent.
        """
        thread_id = str(conversation_id)
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        logger.info("User question: %s", question)
        state = await self.agent.aget_state(config)
        pending_interrupt = get_pending_interrupt(state)
        if pending_interrupt:
            logger.info(
                "Thread %s is awaiting a human decision; returning its interrupt.",
                thread_id,
            )
            return {
                "response": None,
                "interrupt": pending_interrupt,
            }

        persisted_history = self.message_repository.list_by_conversation(conversation_id)
        self.message_repository.create(conversation_id, "user", question)

        checkpoint_messages = state.values.get("messages", {}) if state.values else {}
        context_message = {
            "role": "system",
            "content": f"The active conversation ID is {conversation_id}. Use it for document tools.",
        }
        input_messages = [context_message, {"role": "user", "content": question}]
        if not checkpoint_messages and persisted_history:
            input_messages = [context_message] + [
                {"role": message.role, "content": message.content}
                for message in persisted_history
            ] + [{"role": "user", "content": question}]

        result = await self.agent.ainvoke(
            {
                "messages": input_messages,
            },
            config=config,
            version="v2",
        )

        if result.interrupts:
            logger.info("Human approval required.")
            return {
                "interrupt": result.interrupts[0].value,
            }

        response = result.value["messages"][-1].content
        response = ensure_source_citations(response, result.value["messages"])
        response = ensure_academic_citations(response, result.value["messages"])
        self.message_repository.create(conversation_id, "assistant", response)

        logger.info("Agent response generated.")

        return {
            "response": response,
        }

    async def resume(
        self,
        conversation_id: int,
        decision: str,
        message: str | None = None,
    ):
        """
        Resume an interrupted workflow.

        decision:
            approve
            reject
        """
        thread_id = str(conversation_id)
        
        logger.info(
            "Resuming thread %s with decision '%s'",
            thread_id,
            decision,
        )

        payload = {
            "type": decision,
        }

        if message:
            payload["message"] = message

        result = await self.agent.ainvoke(
            Command(
                resume={
                    "decisions": [
                        payload,
                    ]
                }
            ),
            config={
                "configurable": {
                    "thread_id": thread_id,
                }
            },
            version="v2",
        )


        logger.info("Workflow resumed successfully.")

        response = result.value["messages"][-1].content
        self.message_repository.create(conversation_id, "assistant", response)

        return {
            "response": response,
            "interrupt": None,
        }
