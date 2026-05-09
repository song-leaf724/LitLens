from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notes import NoteGenerateRequest, NoteGenerateResponse
from app.services.note_service import note_service

router = APIRouter()


@router.post("/generate", response_model=NoteGenerateResponse)
async def generate_notes(
    request: NoteGenerateRequest, db: Session = Depends(get_db)
) -> NoteGenerateResponse:
    answer, citations = await note_service.generate_notes(
        db=db,
        document_id=request.document_id,
        focus=request.focus,
        top_k=request.top_k,
    )
    return NoteGenerateResponse(answer=answer, citations=citations)

