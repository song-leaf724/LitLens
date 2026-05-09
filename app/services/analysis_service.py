from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.prompts.templates import build_literature_messages
from app.rag.retriever import format_citations_for_prompt, retrieve_relevant_chunks
from app.schemas.rag import Citation
from app.services.llm_service import llm_service


DEFAULT_ANALYSIS_QUERIES = {
    "plot": "请检索作品的主要情节、关键事件、章节内容、冲突和叙事线索。",
    "characters": "请检索作品中的主要人物、人物关系、性格、动机和象征意义。",
    "themes": "请检索作品的核心主题、意象、隐喻、象征和情绪氛围。",
    "notes": "请检索作品概览、人物关系、主题意象、精彩摘录和可思考问题。",
    "qa": "请检索与用户问题最相关的原文片段。",
}


class AnalysisService:
    async def run_analysis(
        self,
        db: Session,
        task_type: str,
        query: Optional[str] = None,
        document_id: Optional[str] = None,
        passage: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Tuple[str, List[Citation]]:
        retrieval_query = query or DEFAULT_ANALYSIS_QUERIES.get(task_type, "文学分析")
        citations: List[Citation] = []

        if document_id:
            citations = await retrieve_relevant_chunks(
                query=retrieval_query,
                db=db,
                document_id=document_id,
                top_k=top_k,
            )

        if task_type in {"close_reading", "bilingual"} and not passage and citations:
            passage = "\n\n".join(citation.content for citation in citations[:2])

        context = format_citations_for_prompt(citations)
        messages = build_literature_messages(
            task_type=task_type,
            user_input=query or retrieval_query,
            context=context,
            passage=passage,
        )
        answer = await llm_service.chat_completion(messages)
        return answer, citations


analysis_service = AnalysisService()
