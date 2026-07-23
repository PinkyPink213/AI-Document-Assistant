import re
from pathlib import Path

from langchain_classic.retrievers import MultiQueryRetriever
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sqlmodel import Session, select

from app.ai.embeddings import get_embeddings
from app.ai.llm import get_llm
from app.ai.prompts import build_multi_query_prompt
from app.ai.vectorstore import get_qdrant_client, get_vectorstore
from app.db.database import engine
from app.models import Document


def list_conversation_filenames(conversation_id: int) -> list[str]:
    with Session(engine) as session:
        statement = (
            select(Document.filename)
            .where(Document.conversation_id == conversation_id)
            .distinct()
            .order_by(Document.filename)
        )
        return list(session.exec(statement).all())


def resolve_mentioned_filename(question: str, filenames: list[str]) -> str | None:
    normalized_question = question.casefold()
    for filename in sorted(filenames, key=len, reverse=True):
        normalized_filename = filename.casefold()
        if normalized_filename in normalized_question:
            return filename

        stem = Path(filename).stem.casefold()
        if len(stem) >= 3 and re.search(
            rf"(?<![\w-]){re.escape(stem)}(?![\w-])",
            normalized_question,
        ):
            return filename
    return None


def build_document_filter(conversation_id: int, filename: str | None = None) -> Filter:
    conditions = [
        FieldCondition(
            key="metadata.conversation_id",
            match=MatchValue(value=conversation_id),
        )
    ]
    if filename:
        conditions.append(
            FieldCondition(
                key="metadata.filename",
                match=MatchValue(value=filename),
            )
        )
    return Filter(must=conditions)


def retrieve_documents(question: str, conversation_id: int) -> str:
    client = get_qdrant_client()
    filenames = list_conversation_filenames(conversation_id)
    filename = resolve_mentioned_filename(question, filenames)
    vector_store = get_vectorstore(client, get_embeddings())
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": build_document_filter(conversation_id, filename),
        }
    )
    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=retriever,
        llm=get_llm(),
        prompt=build_multi_query_prompt(),
    )
    documents = multi_query_retriever.invoke(question)

    if not documents:
        scope = f"'{filename}'" if filename else "this conversation's uploaded documents"
        return f"No relevant content was found in {scope}."

    return "\n\n".join(document.page_content for document in documents)
