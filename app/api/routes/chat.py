import json
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.prompts.templates import build_literature_messages
from app.rag.retriever import format_citations_for_prompt, retrieve_relevant_chunks
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.rag import Citation
from app.services.chat_service import chat_service
from app.services.llm_service import llm_service
from app.services.session_service import session_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session_id, answer, citations = await chat_service.chat(
        db=db,
        message=request.message,
        session_id=request.session_id,
        document_id=request.document_id,
        use_rag=request.use_rag,
        task_type=request.task_type,
    )
    return ChatResponse(session_id=session_id, answer=answer, citations=citations)


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    session = session_service.ensure_session(db, session_id=request.session_id)
    history = session_service.history_for_prompt(db, session.id)
    session_service.add_message(
        db,
        session_id=session.id,
        role="user",
        content=request.message,
        task_type=request.task_type,
        use_rag=request.use_rag,
    )

    citations: List[Citation] = []
    if request.use_rag and request.document_id:
        citations = await retrieve_relevant_chunks(
            query=request.message,
            db=db,
            document_id=request.document_id,
        )

    context = format_citations_for_prompt(citations) if request.use_rag else ""
    messages = build_literature_messages(
        task_type=request.task_type,
        user_input=request.message,
        context=context,
        history=history,
    )

    async def event_generator():
        full_answer: List[str] = []
        metadata = {"session_id": session.id, "citations": [c.dict() for c in citations]}
        yield f"event: meta\ndata: {json.dumps(metadata, ensure_ascii=False)}\n\n"
        async for token in llm_service.stream_chat_completion(messages):
            full_answer.append(token)
            data = json.dumps({"delta": token}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        answer = "".join(full_answer)
        session_service.add_message(
            db,
            session_id=session.id,
            role="assistant",
            content=answer,
            task_type=request.task_type,
            use_rag=request.use_rag,
        )
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

