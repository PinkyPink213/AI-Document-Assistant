"""Recover PostgreSQL document rows from Qdrant payload metadata."""

from collections import defaultdict

from sqlmodel import Session, select

from app.ai.vectorstore import get_qdrant_client
from app.core.config.settings import settings
from app.db.database import engine
from app.models import Document


def recover() -> int:
    client = get_qdrant_client()
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {"conversation_id": 0, "filename": "", "chunks": 0}
    )
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection_name,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            metadata = (point.payload or {}).get("metadata", {})
            document_id = metadata.get("document_id")
            conversation_id = metadata.get("conversation_id")
            filename = metadata.get("filename")
            if not document_id or not conversation_id or not filename:
                continue
            group = grouped[str(document_id)]
            group["conversation_id"] = int(conversation_id)
            group["filename"] = str(filename)
            group["chunks"] = int(group["chunks"]) + 1
        if offset is None:
            break

    recovered = 0
    with Session(engine) as session:
        for vector_document_id, metadata in grouped.items():
            existing = session.exec(
                select(Document).where(Document.vector_document_id == vector_document_id)
            ).first()
            if existing:
                continue
            session.add(
                Document(
                    conversation_id=int(metadata["conversation_id"]),
                    filename=str(metadata["filename"]),
                    chunk_count=int(metadata["chunks"]),
                    vector_document_id=vector_document_id,
                )
            )
            recovered += 1
        session.commit()

    return recovered


if __name__ == "__main__":
    print(f"Recovered {recover()} document record(s).")
