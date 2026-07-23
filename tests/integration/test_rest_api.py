from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient

from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.documents import router as document_router
from app.api.health import router as health_router
from app.dependencies import get_agent_service, get_conversation_service, get_document_service
from app.services.document_service import DocumentAlreadyExistsError


class FakeConversationService:
    def __init__(self):
        now = datetime.now(UTC)
        self.conversations: dict[int, dict[str, Any]] = {
            1: {
                "id": 1,
                "title": "Existing conversation",
                "created_at": now,
                "updated_at": now,
            }
        }
        self.next_id = 2

    def create(self, request):
        now = datetime.now(UTC)
        conversation = {
            "id": self.next_id,
            "title": request.title,
            "created_at": now,
            "updated_at": now,
        }
        self.conversations[self.next_id] = conversation
        self.next_id += 1
        return conversation

    def get_all(self):
        return list(self.conversations.values())

    def get_by_id(self, conversation_id: int):
        return self.conversations[conversation_id]

    def update(self, conversation_id: int, request):
        self.conversations[conversation_id]["title"] = request.title
        self.conversations[conversation_id]["updated_at"] = datetime.now(UTC)
        return self.conversations[conversation_id]

    async def delete(self, conversation_id: int):
        self.conversations.pop(conversation_id, None)


class FakeAgentService:
    def list_messages(self, conversation_id: int):
        now = datetime.now(UTC)
        return [
            {
                "id": 1,
                "conversation_id": conversation_id,
                "role": "user",
                "content": "Previous question",
                "created_at": now,
            },
            {
                "id": 2,
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": "Previous answer",
                "created_at": now,
            },
        ]

    async def chat(self, conversation_id: int, question: str):
        if conversation_id == 404:
            raise ValueError("Invalid conversation")
        if question == "server error":
            raise RuntimeError("Agent failed")
        return {"response": f"Answer: {question}", "interrupt": None}

    async def resume(self, conversation_id: int, decision: str, message: str | None = None):
        return {"response": f"Resumed with {decision}", "interrupt": None}


class FakeDocumentService:
    def __init__(self):
        now = datetime.now(UTC)
        self.documents: dict[int, dict[str, Any]] = {
            10: {
                "id": 10,
                "conversation_id": 1,
                "filename": "existing.pdf",
                "created_at": now,
                "updated_at": now,
            }
        }

    async def upload_document(self, conversation_id: int, pdf_bytes: bytes, filename: str):
        if any(
            document["conversation_id"] == conversation_id
            and document["filename"].casefold() == filename.casefold()
            for document in self.documents.values()
        ):
            raise DocumentAlreadyExistsError(
                f"'{filename}' is already uploaded in this conversation."
            )
        document_id = max(self.documents) + 1
        now = datetime.now(UTC)
        document = {
            "id": document_id,
            "conversation_id": conversation_id,
            "filename": filename,
            "created_at": now,
            "updated_at": now,
        }
        self.documents[document_id] = document
        return document

    def list_documents(self, conversation_id: int):
        return [
            document
            for document in self.documents.values()
            if document["conversation_id"] == conversation_id
        ]

    def get_document(self, document_id: int):
        return self.documents.get(document_id)

    def delete_document(self, document_id: int):
        return self.documents.pop(document_id, None) is not None


@pytest.fixture
def api_app():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    conversation_service = FakeConversationService()
    document_service = FakeDocumentService()
    app.dependency_overrides[get_conversation_service] = lambda: conversation_service
    app.dependency_overrides[get_document_service] = lambda: document_service
    app.dependency_overrides[get_agent_service] = lambda: FakeAgentService()
    app.include_router(chat_router)
    app.include_router(conversation_router)
    app.include_router(document_router)
    app.include_router(health_router)
    return app


@pytest.fixture
async def client(api_app):
    transport = ASGITransport(app=api_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_conversation_crud(client):
    created = await client.post("/conversation", json={"title": "Risk review"})
    assert created.status_code == 200
    conversation_id = created.json()["id"]

    listed = await client.get("/conversation")
    assert listed.status_code == 200
    assert any(item["id"] == conversation_id for item in listed.json())

    fetched = await client.get(f"/conversation/{conversation_id}")
    assert fetched.json()["title"] == "Risk review"

    updated = await client.put(f"/conversation/{conversation_id}", json={"title": "Risk review updated"})
    assert updated.json()["title"] == "Risk review updated"

    deleted = await client.delete(f"/conversation/{conversation_id}")
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_chat_send_continue_and_errors(client):
    history = await client.get("/conversations/1/messages")
    assert history.status_code == 200
    assert [message["role"] for message in history.json()] == ["user", "assistant"]

    response = await client.post("/conversations/1/chat", json={"conversation_id": 1, "message": "hello"})
    assert response.status_code == 200
    assert response.json()["response"] == "Answer: hello"

    continued = await client.post(
        "/conversations/1/chat/resume",
        json={"conversation_id": 1, "decision": "approve", "message": None},
    )
    assert continued.status_code == 200
    assert continued.json()["response"] == "Resumed with approve"

    empty = await client.post("/conversations/1/chat", json={"conversation_id": 1, "message": ""})
    assert empty.status_code == 422

    invalid = await client.post("/conversations/404/chat", json={"conversation_id": 404, "message": "x"})
    assert invalid.status_code == 500

    failed = await client.post(
        "/conversations/1/chat",
        json={"conversation_id": 1, "message": "server error"},
    )
    assert failed.status_code == 500


@pytest.mark.asyncio
async def test_document_upload_list_delete_and_validation(client):
    uploaded = await client.post(
        "/1/documents",
        files={"file": ("brief.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert uploaded.status_code == 200
    document_id = uploaded.json()["id"]

    duplicate = await client.post(
        "/1/documents",
        files={"file": ("BRIEF.PDF", b"%PDF-1.4", "application/pdf")},
    )
    assert duplicate.status_code == 409
    assert "already uploaded" in duplicate.json()["detail"]

    invalid = await client.post(
        "/1/documents",
        files={"file": ("brief.txt", b"text", "text/plain")},
    )
    assert invalid.status_code == 400

    spoofed_pdf = await client.post(
        "/1/documents",
        files={"file": ("malware.pdf", b"MZ executable", "application/pdf")},
    )
    assert spoofed_pdf.status_code == 400
    assert "content is not a valid PDF" in spoofed_pdf.json()["detail"]

    oversized = await client.post(
        "/1/documents",
        files={"file": ("large.pdf", b"0" * (20 * 1024 * 1024 + 1), "application/pdf")},
    )
    assert oversized.status_code == 413

    listed = await client.get("/1/documents")
    assert listed.status_code == 200
    assert any(item["id"] == document_id for item in listed.json())

    deleted = await client.delete(f"/documents/{document_id}")
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Document deleted successfully."


@pytest.mark.asyncio
async def test_health_endpoints(client):
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    database = await client.get("/health/db")
    assert database.status_code == 200
    assert database.json()["status"] in {"ok", "error"}


@pytest.mark.asyncio
async def test_frontend_cors_preflight(client):
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
