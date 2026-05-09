from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatMessageResponse
from app.services.session_service import session_service

router = APIRouter()


@router.get("/{session_id}/messages", response_model=list[ChatMessageResponse])
def list_session_messages(
    session_id: str, db: Session = Depends(get_db)
) -> list[ChatMessageResponse]:
    messages = session_service.list_messages(db, session_id)
    return [
        ChatMessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            task_type=message.task_type,
            use_rag=message.use_rag,
            created_at=message.created_at.isoformat(),
        )
        for message in messages
    ]

