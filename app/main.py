from fastapi import FastAPI
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from contextlib import asynccontextmanager
from app.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):

    create_db_and_tables()

    yield


app = FastAPI(
    lifespan=lifespan,
)

# app.include_router(chat_router)
# app.include_router(conversation_router)

