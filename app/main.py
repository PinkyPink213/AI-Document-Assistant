import logging
import re
import time
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.documents import router as document_router
from app.api.health import router as health_router
from contextlib import asynccontextmanager

from app.ai import (
    build_agent,
    build_delete_document_workflow,
    postgres_checkpointer,
)
from app.core.config import settings
from app.core.config.startup import startup
from app.core.rate_limit import RateLimitMiddleware
from app.core.observability import (
    application_metrics,
    bind_request_context,
    request_id_context,
    reset_request_context,
)
from app.services.agent_service import ConversationNotFoundError

logger = logging.getLogger("observability.http")
CONVERSATION_PATH_PATTERN = re.compile(
    r"(?:/conversations?/(\d+)|^/(\d+)/documents)"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    startup()
    async with postgres_checkpointer(settings.postgres_url) as checkpointer:
        app.state.agent = build_agent(checkpointer)
        app.state.delete_document_workflow = build_delete_document_workflow(
            checkpointer
        )
        yield


app = FastAPI(
    lifespan=lifespan,
)


@app.exception_handler(ConversationNotFoundError)
async def conversation_not_found_handler(
    _request: Request,
    error: ConversationNotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={"detail": str(error)},
    )


app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.rate_limit_enabled,
    window_seconds=settings.rate_limit_window_seconds,
    default_requests=settings.rate_limit_default_requests,
    chat_requests=settings.rate_limit_chat_requests,
    upload_requests=settings.rate_limit_upload_requests,
)

@app.middleware("http")
async def observe_request(request: Request, call_next):
    request_id = request.headers.get("x-request-id")
    match = CONVERSATION_PATH_PATTERN.search(request.url.path)
    matched_conversation = (
        next((value for value in match.groups() if value), None)
        if match
        else None
    )
    conversation_id = (
        int(matched_conversation) if matched_conversation else None
    )
    tokens = bind_request_context(request_id, conversation_id)
    started = time.perf_counter()
    failed = False
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        failed = status_code >= 500
        response.headers["x-request-id"] = request_id_context.get()
        return response
    except Exception:
        failed = True
        logger.exception(
            "HTTP request failed",
            extra={"event": "http.failed", "path": request.url.path},
        )
        raise
    finally:
        metrics = application_metrics.record_request(failed)
        logger.info(
            "HTTP request completed",
            extra={
                "event": "http.completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "request_latency_ms": round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
                **metrics,
            },
        )
        reset_request_context(tokens)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(document_router)
app.include_router(health_router)
#  uv run uvicorn app.main:app --reload  
# uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
