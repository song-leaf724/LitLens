from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.rag.parser import UnsupportedDocumentError
from app.schemas.documents import DocumentDeleteResponse, DocumentListResponse, DocumentResponse
from app.services.document_service import document_service

router = APIRouter()


def document_to_response(document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        status=document.status,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at.isoformat(),
        title=document.title,
        author=document.author,
        source_name=document.source_name,
        source_id=document.source_id,
        source_url=document.source_url,
        license=document.license,
        document_type=document.document_type,
        type_confidence=document.type_confidence,
        type_reason=document.type_reason,
        chunk_strategy=document.chunk_strategy,
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
    return document_to_response(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    documents = document_service.list_documents(db)
    return DocumentListResponse(
        documents=[document_to_response(document) for document in documents]
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDeleteResponse:
    deleted = document_service.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="没有找到这个文本，可能已经被删除。")
    return DocumentDeleteResponse(id=document_id)
