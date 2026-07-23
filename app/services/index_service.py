from pathlib import Path

from app.ai import (
    load_pdf,
    split_documents,
    enrich_metadata,
)

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

class IndexService:
    """
    Service responsible for indexing PDF documents into the vector database.
    """
    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def index_pdf(
        self,
        conversation_id: int,
        pdf_bytes: bytes,
        filename: str,
        document_id: str,
    ) -> int:
        """
        Load a PDF, split it into chunks, enrich metadata,
        and index the chunks into Qdrant.
        """

        documents = load_pdf(pdf_bytes,filename)
        chunks = split_documents(documents)
        chunks = enrich_metadata(
            conversation_id=conversation_id,
            chunks=chunks,
            filename=filename,
            document_id=document_id,
        )

        self.vector_store.add_documents(chunks)
        return len(chunks)

    # async def reindex_pdf(self, pdf_path: Path) -> None:
    #     """
    #     Re-index a PDF document.
    #     Future implementation can remove old vectors first.
    #     """
    #     await self.index_pdf(pdf_path)
    
    def delete_document(self, document_id: str) -> None:
        self.vector_store.client.delete(
            collection_name=self.vector_store.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
            wait=True,
        )
