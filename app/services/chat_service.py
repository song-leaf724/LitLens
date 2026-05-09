from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.prompts.templates import build_literature_messages
from app.rag.retriever import format_citations_for_prompt, retrieve_relevant_chunks
from app.schemas.rag import Citation
from app.services.llm_service import llm_service
from app.services.session_service import session_service


class ChatService:
    async def chat(
        self,
        db: Session,
        message: str,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None,
        use_rag: bool = True,
        task_type: str = "qa",
    ) -> Tuple[str, str, List[Citation]]:
        session = session_service.ensure_session(db, session_id=session_id)
        history = session_service.history_for_prompt(db, session.id)
        session_service.add_message(
            db,
            session_id=session.id,
            role="user",
            content=message,
            task_type=task_type,
            use_rag=use_rag,
        )

        citations: List[Citation] = []
        if use_rag and document_id:
            citations = await retrieve_relevant_chunks(
                query=message,
                db=db,
                document_id=document_id,
            )

        context = format_citations_for_prompt(citations) if use_rag else ""
        messages = build_literature_messages(
            task_type=task_type,
            user_input=message,
            context=context,
            history=history,
        )
        answer = await llm_service.chat_completion(messages)
        session_service.add_message(
            db,
            session_id=session.id,
            role="assistant",
            content=answer,
            task_type=task_type,
            use_rag=use_rag,
        )
        return session.id, answer, citations


chat_service = ChatService()

