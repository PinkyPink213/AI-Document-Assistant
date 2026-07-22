from langchain.tools import tool
from app.ai import get_qdrant_client, retrieve_documents
from app.core.config  import settings
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

@tool
def list_uploaded_documents() -> list[str]:
    """
    Return the names of all uploaded PDF documents.
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

        filename = metadata.get("filename")

        if filename:
            filenames.add(filename)

    return sorted(filenames)


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
def search_documents(question:str)->str:
    """
    Return answer from uploaded PDF documents.

    Use this tool whenever the user asks questions about
    the contents of uploaded documents.
    """ 
    return retrieve_documents(question)

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