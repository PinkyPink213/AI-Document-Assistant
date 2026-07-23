import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.rate_limit import RateLimitMiddleware


@pytest.mark.asyncio
async def test_rejects_requests_over_endpoint_limit():
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        default_requests=10,
        chat_requests=2,
        upload_requests=1,
        window_seconds=60,
    )

    @app.post("/conversations/7/chat")
    async def chat():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        first = await client.post("/conversations/7/chat")
        second = await client.post("/conversations/7/chat")
        blocked = await client.post("/conversations/7/chat")

    assert first.status_code == 200
    assert first.headers["x-ratelimit-remaining"] == "1"
    assert second.headers["x-ratelimit-remaining"] == "0"
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "60"
    assert blocked.json()["detail"].startswith("Too many requests")


@pytest.mark.asyncio
async def test_exempts_health_checks():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, default_requests=1)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        responses = [await client.get("/health") for _ in range(3)]

    assert all(response.status_code == 200 for response in responses)
