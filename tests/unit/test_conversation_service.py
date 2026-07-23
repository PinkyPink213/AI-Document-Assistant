from types import SimpleNamespace

import pytest

from app.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_delete_conversation_removes_all_related_state(monkeypatch):
    conversation = SimpleNamespace(id=8)
    calls: list[tuple[str, object]] = []

    repository = SimpleNamespace(
        get_by_id=lambda conversation_id: conversation,
        delete=lambda value: calls.append(("conversation", value.id)),
    )
    document_repository = SimpleNamespace(
        delete_by_conversation_id=lambda conversation_id: calls.append(
            ("documents", conversation_id)
        )
    )
    chat_message_repository = SimpleNamespace(
        delete_by_conversation_id=lambda conversation_id: calls.append(
            ("history", conversation_id)
        )
    )

    class QdrantClient:
        def delete(self, **kwargs):
            calls.append(("vectors", kwargs["wait"]))

    class Checkpointer:
        async def adelete_thread(self, thread_id):
            calls.append(("checkpoint", thread_id))

    monkeypatch.setattr(
        "app.services.conversation_service.settings.qdrant_collection_name",
        "documents",
    )
    service = ConversationService(
        repository,
        document_repository,
        chat_message_repository,
        QdrantClient(),
        Checkpointer(),
    )

    await service.delete(8)

    assert ("history", 8) in calls
    assert ("documents", 8) in calls
    assert ("conversation", 8) in calls
    assert ("vectors", True) in calls
    assert ("checkpoint", "8") in calls
    assert ("checkpoint", "conversation:8:document-deletion") in calls
