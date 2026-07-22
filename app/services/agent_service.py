import logging

from langgraph.types import Command

from app.ai.agent import agent

logger = logging.getLogger(__name__)

class AgentService:
    """
    Service responsible for interacting with the LangGraph Agent.
    """

    def __init__(self):
        self.agent = agent

    async def chat(
        self,
        conversation_id: int,
        question: str, 
    ):
        """
        Send a user message to the agent.
        """
        thread_id = str(conversation_id)
        logger.info("User question: %s", question)

        result = self.agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": question,
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id,
                }
            },
            version="v2",
        )

        if result.interrupts:
            logger.info("Human approval required.")
            return {
                "interrupt": result.interrupts[0].value,
            }

        response = result.value["messages"][-1].content

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

        return {
            "response": result.value["messages"][-1].content,
            "interrupt": None,
        }