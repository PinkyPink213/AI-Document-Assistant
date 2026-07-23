from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from app.dependencies import  DocumentServiceDep
from app.dependencies import get_conversation_service
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
)
from app.services import ConversationService
from app.services.document_service import DocumentAlreadyExistsError
from app.core.security import has_valid_pdf_signature

router = APIRouter()
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.post("/conversation",response_model=ConversationResponse,)
def create_conversation(request: ConversationCreate, service: Annotated[ConversationService,Depends(get_conversation_service), ],):

    return service.create(request)


@router.get( "/conversation",response_model=list[ConversationResponse])
def get_all(service: Annotated[ConversationService,Depends(get_conversation_service)]):

    return service.get_all()


@router.get("/conversation/{conversation_id}",response_model=ConversationResponse)
def get_by_id(
    conversation_id: int,
    service: Annotated[ConversationService, Depends(get_conversation_service)]
):

    return service.get_by_id(conversation_id)
    


@router.put("/conversation/{conversation_id}",response_model=ConversationResponse)
def update(
    conversation_id: int,
    request: ConversationUpdate,
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
):

    return service.update(conversation_id,request)
    


@router.delete("/conversation/{conversation_id}",status_code=204)
async def delete(
    conversation_id: int,
    service: Annotated[
        ConversationService,
        Depends(get_conversation_service),
    ],
):
   
    await service.delete(conversation_id)


@router.post("/{conversation_id}/documents")
async def upload_document(
    conversation_id: int,
    file: UploadFile,
    document_service: DocumentServiceDep,
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDF file is too large.",
        )

    if not has_valid_pdf_signature(pdf_bytes):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file content is not a valid PDF.",
        )

    try:
        return await document_service.upload_document(
            conversation_id=conversation_id,
            pdf_bytes=pdf_bytes,
            filename=file.filename,
        )
    except DocumentAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

@router.get("/{conversation_id}/documents")
def list_documents(
    conversation_id: int,
    document_service: DocumentServiceDep,
):
    return document_service.list_documents(conversation_id)
