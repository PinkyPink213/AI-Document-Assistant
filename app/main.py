from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.documents import router as document_router
from app.api.health import router as health_router
from contextlib import asynccontextmanager

from app.core.config.startup import startup

@asynccontextmanager
async def lifespan(app: FastAPI):
    startup()
    yield


app = FastAPI(
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
