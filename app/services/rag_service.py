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

    async def get_answer(self, question: str):
        logger.info("Retrieving question: %s", question)

        documents = retrieve_documents(question)

        context = "\n\n".join(
            doc.page_content
            for doc in documents
        )

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