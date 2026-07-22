from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_agent_service
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ResumeRequest,
)
from app.services import AgentService

router = APIRouter(
    prefix="/conversations/{conversation_id}",
    tags=["Chat"],
)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    conversation_id: int,
    request: ChatRequest,
    service: Annotated[
        AgentService,
        Depends(get_agent_service),
    ],
):
    """
    Send a message to the AI agent.
    """

    return await service.chat(
        conversation_id=conversation_id,
        question=request.message,
    )


@router.post("/chat/resume", response_model=ChatResponse)
async def resume(
    conversation_id: int,
    request: ResumeRequest,
    service: Annotated[
        AgentService,
        Depends(get_agent_service),
    ],
):
    """
    Resume an interrupted agent workflow.
    """

    return await service.resume(
        conversation_id=conversation_id,
        decision=request.decision,
        message=request.message,
    )