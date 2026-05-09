from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.rag.parser import UnsupportedDocumentError
from app.schemas.documents import DocumentListResponse, DocumentResponse
from app.services.document_service import document_service

router = APIRouter()


def _document_response(document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        status=document.status,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at.isoformat(),
    )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> DocumentResponse:
    content = await file.read()
    try:
        document = await document_service.upload_document(
            db=db,
            filename=file.filename or "upload.txt",
            content=content,
        )
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _document_response(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    documents = document_service.list_documents(db)
    return DocumentListResponse(
        documents=[_document_response(document) for document in documents]
    )

