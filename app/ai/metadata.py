from langchain_core.documents import Document
import uuid

def enrich_metadata(conversation_id: int,chunks: list[Document],filename: str)-> list[Document]:
    document_id = str(uuid.uuid4())
    
    enriched_chunks = []

    for chunk_index, chunk in enumerate(chunks):

        metadata = {
            **chunk.metadata,
            "document_id": document_id,
            "chunk_id": chunk_index,
            "filename": filename,
            "conversation_id": conversation_id,
        }

        enriched_chunks.append(
            Document(
                page_content=chunk.page_content,
                metadata=metadata,
            )
        )

    return enriched_chunks