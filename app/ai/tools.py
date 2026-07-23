from langchain.tools import tool
from app.ai import get_qdrant_client, retrieve_documents
from app.core.config  import settings
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

@tool
def list_uploaded_documents(conversation_id: int | None = None) -> list[str]:
    """
    Return uploaded PDF filenames, optionally limited to a conversation.
    """
    client = get_qdrant_client()

    filenames = set()

    points, _ = client.scroll(
        collection_name=settings.qdrant_collection_name,
        with_payload=True,
        with_vectors=False,
        limit=1000,
    )

    for point in points:
        payload = point.payload or {}
        metadata = payload.get("metadata", {})
        if (
            conversation_id is not None
            and metadata.get("conversation_id") != conversation_id
        ):
            continue

        filename = metadata.get("filename")

        if filename:
            filenames.add(filename)

    return sorted(filenames)


@tool
def count_uploaded_documents(conversation_id: int) -> int:
    """Return the number of distinct uploaded PDF records for a conversation."""
    client = get_qdrant_client()
    document_ids = set()
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection_name,
            offset=offset,
            with_payload=True,
            with_vectors=False,
            limit=256,
        )
        for point in points:
            metadata = (point.payload or {}).get("metadata", {})
            if metadata.get("conversation_id") == conversation_id:
                document_id = metadata.get("document_id")
                if document_id:
                    document_ids.add(document_id)
        if offset is None:
            break

    return len(document_ids)


@tool
def count_pdf_pages(conversation_id: int,filename: str) -> int:
    """
    Return the total number of pages for a PDF document.
    """
    client = get_qdrant_client()
    print(client.get_collection(settings.qdrant_collection_name).payload_schema)
    points, _ = client.scroll(
        collection_name=settings.qdrant_collection_name,
        with_payload=True,
        with_vectors=False,
        limit=1000,
    )

    for point in points:
        metadata = point.payload.get("metadata", {})
        if (
            metadata.get("conversation_id") == conversation_id
            and metadata.get("filename") == filename
        ):
            return metadata.get("total_pages", 0)

    return 0

@tool
def search_documents(question: str, conversation_id: int) -> str:
    """
    Retrieve relevant content from PDFs in the active conversation.

    If the question mentions an uploaded filename or its stem, retrieval is
    limited to that file. Otherwise all PDFs in the conversation are searched.
    """
    return retrieve_documents(question, conversation_id)

@tool
def delete_document(filename: str) -> str:
    """
    Delete an uploaded PDF document from Qdrant.
    """

    client = get_qdrant_client()

    client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="metadata.filename",
                    match=MatchValue(value=filename),
                )
            ]
        ),
        wait=True,
    )

    return f"Deleted '{filename}'"
