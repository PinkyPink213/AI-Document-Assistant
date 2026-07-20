from fastapi import FastAPI
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    lifespan=lifespan,
)

app.include_router(chat_router)
app.include_router(conversation_router)

