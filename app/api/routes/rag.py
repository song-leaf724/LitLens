from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.prompts.templates import build_literature_messages
from app.rag.retriever import format_citations_for_prompt, retrieve_relevant_chunks
from app.schemas.rag import RagQueryRequest, RagQueryResponse
from app.services.llm_service import llm_service

router = APIRouter()


@router.post("/query", response_model=RagQueryResponse)
async def rag_query(
    request: RagQueryRequest, db: Session = Depends(get_db)
) -> RagQueryResponse:
    citations = await retrieve_relevant_chunks(
        query=request.query,
        db=db,
        document_id=request.document_id,
        top_k=request.top_k,
    )
    context = format_citations_for_prompt(citations)
    messages = build_literature_messages(
        task_type=request.task_type,
        user_input=request.query,
        context=context,
    )
    answer = await llm_service.chat_completion(messages)
    return RagQueryResponse(answer=answer, citations=citations)

