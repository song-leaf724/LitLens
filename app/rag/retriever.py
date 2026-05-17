from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Chunk, Document
from app.rag.embeddings import embedding_service
from app.rag.vector_store import vector_store
from app.schemas.rag import Citation


async def retrieve_relevant_chunks(
    query: str,
    db: Session,
    document_id: Optional[str] = None,
    top_k: Optional[int] = None,
) -> List[Citation]:
    embedding = await embedding_service.embed_query(query)
    hits = vector_store.query(
        embedding=embedding,
        top_k=top_k or settings.retrieval_top_k,
        document_id=document_id,
    )

    citations: List[Citation] = []
    for hit in hits:
        chunk_id = hit.metadata.get("chunk_id")
        chunk = db.get(Chunk, chunk_id) if chunk_id else None
        if not chunk:
            continue
        document = db.get(Document, chunk.document_id)
        citations.append(
            Citation(
                document_id=chunk.document_id,
                filename=document.filename if document else "unknown",
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                source_location=chunk.source_location,
                content=chunk.content,
                score=hit.score,
                document_type=document.document_type if document else "unknown",
                chunk_type=chunk.chunk_type,
                section_title=chunk.section_title,
                title=document.title if document else None,
                author=document.author if document else None,
                source_name=document.source_name if document else None,
                source_url=document.source_url if document else None,
            )
        )
    return citations


def format_citations_for_prompt(citations: List[Citation]) -> str:
    if not citations:
        return "未检索到可用原文片段。"

    blocks = []
    total_chars = 0
    for index, citation in enumerate(citations, start=1):
        content = citation.content.strip()
        if total_chars + len(content) > settings.max_context_chars:
            content = content[: max(0, settings.max_context_chars - total_chars)]
        total_chars += len(content)
        location = _format_location(citation)
        blocks.append(
            "[引用 {index}] 作品：{title}；作者：{author}；文件：{filename}；体裁：{document_type}；位置：{location}；片段：\n{content}".format(
                index=index,
                title=citation.title or citation.filename,
                author=citation.author or "未知",
                filename=citation.filename,
                document_type=citation.document_type,
                location=location,
                content=content,
            )
        )
        if total_chars >= settings.max_context_chars:
            break
    return "\n\n".join(blocks)


def _format_location(citation: Citation) -> str:
    if citation.section_title:
        return f"{citation.section_title} / {citation.chunk_type} / {citation.source_location}"
    return f"{citation.chunk_type} / {citation.source_location}"
