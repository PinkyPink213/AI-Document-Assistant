import logging

from langgraph.types import Command

from app.ai.agent import agent
from app.repositories import ChatMessageRepository

logger = logging.getLogger(__name__)

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
        persisted_history = self.message_repository.list_by_conversation(conversation_id)
        self.message_repository.create(conversation_id, "user", question)

        state = self.agent.get_state(config)
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

        result = self.agent.invoke(
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

        result = self.agent.invoke(
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
