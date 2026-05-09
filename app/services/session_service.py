from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ChatSession, Message


class SessionService:
    def ensure_session(
        self, db: Session, session_id: Optional[str] = None, title: Optional[str] = None
    ) -> ChatSession:
        if session_id:
            session = db.get(ChatSession, session_id)
            if session:
                return session

        session = ChatSession(title=title or "文学阅读会话")
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def add_message(
        self,
        db: Session,
        session_id: str,
        role: str,
        content: str,
        task_type: str = "chat",
        use_rag: bool = False,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            task_type=task_type,
            use_rag=use_rag,
        )
        session = db.get(ChatSession, session_id)
        if session:
            session.updated_at = datetime.utcnow()
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def list_messages(self, db: Session, session_id: str) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def history_for_prompt(
        self, db: Session, session_id: str, limit: int = 6
    ) -> List[Dict[str, str]]:
        messages = self.list_messages(db, session_id)[-limit:]
        return [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in {"user", "assistant"}
        ]


session_service = SessionService()

