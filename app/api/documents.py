from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends

from app.core.config import settings
from app.dependencies import  DocumentServiceDep

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# @router.post("/upload")
# async def upload_document(
#     file: UploadFile,
#     document_service: DocumentServiceDep,
# ):
#     if file.content_type != "application/pdf":
#         raise HTTPException(
#             status_code=400,
#             detail="Only PDF files are supported.",
#         )

#     pdf_bytes = await file.read()

#     return await document_service.upload_document(
#         pdf_bytes=pdf_bytes,
#         filename=file.filename,
#     )


# @router.get("")
# def list_documents(document_service: DocumentServiceDep):
#     return document_service.list_documents()


@router.get("/{document_id}")
def get_document(document_id: int, document_service: DocumentServiceDep):
    document = document_service.get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


@router.delete("/{document_id}")
def delete_document(document_id: int, document_service: DocumentServiceDep,):
    success = document_service.delete_document(document_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "message": "Document deleted successfully."
    }