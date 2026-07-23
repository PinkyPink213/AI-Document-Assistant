import logging

from app.ai import (
    build_rag_prompt,
    get_llm,
    retrieve_documents,
)

logger = logging.getLogger(__name__)


class RagService:
    """
    Service responsible for answering user questions using RAG.
    """
    def __init__(self):
        self.llm = get_llm()

    async def get_answer(self, question: str, conversation_id: int):
        logger.info("Retrieving question: %s", question)

        context = retrieve_documents(question, conversation_id)

        prompt = build_rag_prompt()

        messages = prompt.invoke(
            {
                "context": context,
                "question": question,
            }
        )

        response = self.llm.invoke(messages)

        logger.info("Generated response successfully.")

        return response
