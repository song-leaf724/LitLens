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
        blocks.append(
            "[引用 {index}] 文件：{filename}；位置：{location}；片段：\n{content}".format(
                index=index,
                filename=citation.filename,
                location=citation.source_location,
                content=content,
            )
        )
        if total_chars >= settings.max_context_chars:
            break
    return "\n\n".join(blocks)

