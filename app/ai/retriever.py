import logging
import re
import time
from pathlib import Path

from langchain_core.documents import Document as LangChainDocument
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from pydantic import BaseModel, Field
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue
from sqlmodel import Session, select

from app.ai.embeddings import get_embeddings
from app.ai.llm import get_llm
from app.ai.vectorstore import get_qdrant_client, get_vectorstore
from app.db.database import engine
from app.models import Document

logger = logging.getLogger(__name__)

class RerankSelection(BaseModel):
    chunk_ids: list[int] = Field(
        description="Candidate chunk IDs ordered from most to least relevant."
    )


def list_conversation_filenames(conversation_id: int) -> list[str]:
    with Session(engine) as session:
        statement = (
            select(Document.filename)
            .where(Document.conversation_id == conversation_id)
            .distinct()
            .order_by(Document.filename)
        )
        return list(session.exec(statement).all())


def list_conversation_vector_document_ids(conversation_id: int) -> list[str]:
    """Return the Qdrant document IDs that are still active in PostgreSQL."""
    with Session(engine) as session:
        statement = select(Document.vector_document_id).where(
            Document.conversation_id == conversation_id
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


def build_document_filter(
    conversation_id: int,
    filename: str | None = None,
    active_document_ids: list[str] | None = None,
) -> Filter:
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
    if active_document_ids is not None:
        conditions.append(
            FieldCondition(
                key="metadata.document_id",
                match=MatchAny(any=active_document_ids),
            )
        )
    return Filter(must=conditions)


def rerank_documents(
    question: str,
    documents: list[LangChainDocument],
    limit: int = 6,
) -> list[LangChainDocument]:
    if len(documents) <= limit:
        return documents

    candidates = "\n\n".join(
        (
            f"CHUNK {index}\n"
            f"File: {document.metadata.get('filename', 'unknown')}\n"
            f"Page: {document.metadata.get('page', 'unknown')}\n"
            f"Content:\n{document.page_content}"
        )
        for index, document in enumerate(documents)
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Rank document chunks by their usefulness for answering the question. "
                "Prioritize direct evidence, exact facts, and complete context. "
                "Return only unique candidate chunk IDs, best first.",
            ),
            ("human", "Question:\n{question}\n\nCandidates:\n{candidates}"),
        ]
    )

    try:
        reranker = get_llm().with_structured_output(RerankSelection)
        selection = reranker.invoke(
            prompt.invoke({"question": question, "candidates": candidates})
        )
        selected_ids: list[int] = []
        for chunk_id in selection.chunk_ids:
            if 0 <= chunk_id < len(documents) and chunk_id not in selected_ids:
                selected_ids.append(chunk_id)
            if len(selected_ids) == limit:
                break
        for chunk_id in range(len(documents)):
            if len(selected_ids) == limit:
                break
            if chunk_id not in selected_ids:
                selected_ids.append(chunk_id)
        return [documents[chunk_id] for chunk_id in selected_ids]
    except Exception:
        return documents[:limit]


def format_cited_context(documents: list[LangChainDocument]) -> str:
    sections = []
    for index, document in enumerate(documents, start=1):
        filename = document.metadata.get("filename", "unknown")
        page = document.metadata.get("page", "unknown")
        sections.append(
            f"[SOURCE {index}: {filename}, page {page}]\n{document.page_content}"
        )
    return "\n\n".join(sections)


@traceable(name="retrieve_documents", run_type="retriever")
def retrieve_documents(question: str, conversation_id: int) -> str:
    started = time.perf_counter()
    client = get_qdrant_client()
    filenames = list_conversation_filenames(conversation_id)
    active_document_ids = list_conversation_vector_document_ids(conversation_id)
    if not active_document_ids:
        logger.info(
            "Document retrieval completed",
            extra={
                "event": "retrieval.completed",
                "retrieval_latency_ms": round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
                "candidate_count": 0,
                "selected_count": 0,
                "filename_filter": None,
            },
        )
        return (
            "No documents are currently uploaded to this conversation, "
            "so no supporting information was found."
        )

    filename = resolve_mentioned_filename(question, filenames)
    vector_store = get_vectorstore(client, get_embeddings())
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 20,
            "filter": build_document_filter(
                conversation_id,
                filename,
                active_document_ids,
            ),
        }
    )
    candidates = retriever.invoke(question)

    if not candidates:
        scope = f"'{filename}'" if filename else "this conversation's uploaded documents"
        logger.info(
            "Document retrieval completed",
            extra={
                "event": "retrieval.completed",
                "retrieval_latency_ms": round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
                "candidate_count": 0,
                "selected_count": 0,
                "filename_filter": filename,
            },
        )
        return f"No relevant content was found in {scope}."

    documents = rerank_documents(question, candidates, limit=6)
    logger.info(
        "Document retrieval completed",
        extra={
            "event": "retrieval.completed",
            "retrieval_latency_ms": round(
                (time.perf_counter() - started) * 1000,
                2,
            ),
            "candidate_count": len(candidates),
            "selected_count": len(documents),
            "filename_filter": filename,
        },
    )
    return format_cited_context(documents)
