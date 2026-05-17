import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Chunk, Document
from app.rag.chunk_strategies import chunk_by_strategy
from app.rag.document_type import document_type_detector
from app.rag.embeddings import embedding_service
from app.rag.parser import parse_document
from app.rag.vector_store import VectorRecord, vector_store


@dataclass
class DocumentIngestMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    source_name: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None


class DocumentService:
    async def upload_document(
        self, db: Session, filename: str, content: bytes
    ) -> Document:
        text = parse_document(filename, content)
        return await self.ingest_text(
            db=db,
            filename=filename,
            text=text,
            raw_content=content,
            metadata=DocumentIngestMetadata(title=os.path.splitext(filename)[0]),
        )

    async def import_text(
        self,
        db: Session,
        filename: str,
        text: str,
        metadata: Optional[DocumentIngestMetadata] = None,
    ) -> Document:
        return await self.ingest_text(
            db=db,
            filename=filename,
            text=text,
            raw_content=text.encode("utf-8"),
            metadata=metadata or DocumentIngestMetadata(title=os.path.splitext(filename)[0]),
        )

    async def ingest_text(
        self,
        db: Session,
        filename: str,
        text: str,
        raw_content: bytes,
        metadata: Optional[DocumentIngestMetadata] = None,
    ) -> Document:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            raise ValueError("文档内容为空，无法进行文学分析。")

        metadata = metadata or DocumentIngestMetadata(title=os.path.splitext(filename)[0])
        os.makedirs(settings.upload_dir, exist_ok=True)

        document_id = str(uuid.uuid4())
        safe_name = self._safe_filename(filename)
        storage_path = os.path.join(settings.upload_dir, f"{document_id}_{safe_name}")

        with open(storage_path, "wb") as file:
            file.write(raw_content)

        detected = document_type_detector.detect(normalized)
        chunk_strategy, text_chunks = chunk_by_strategy(normalized, detected.document_type)

        document = Document(
            id=document_id,
            filename=filename,
            file_type=os.path.splitext(filename)[1].lower().lstrip(".") or "txt",
            storage_path=storage_path,
            status="processing",
            title=metadata.title,
            author=metadata.author,
            source_name=metadata.source_name,
            source_id=metadata.source_id,
            source_url=metadata.source_url,
            license=metadata.license,
            document_type=detected.document_type,
            type_confidence=detected.confidence,
            type_reason=detected.reason,
            chunk_strategy=chunk_strategy,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            if not text_chunks:
                raise ValueError("文档没有可用文本内容，无法切分。")

            chunks: List[Chunk] = []
            for text_chunk in text_chunks:
                chunk_id = str(uuid.uuid4())
                chunk = Chunk(
                    id=chunk_id,
                    document_id=document.id,
                    chunk_index=text_chunk.chunk_index,
                    content=text_chunk.content,
                    source_location=(
                        f"chars:{text_chunk.start_char}-{text_chunk.end_char}"
                    ),
                    vector_id=f"{document.id}:{text_chunk.chunk_index}",
                    chunk_type=text_chunk.chunk_type,
                    section_title=text_chunk.section_title,
                    metadata_json=json.dumps(text_chunk.metadata or {}, ensure_ascii=False),
                )
                chunks.append(chunk)
                db.add(chunk)
            db.commit()

            embeddings = await embedding_service.embed_texts(
                [chunk.content for chunk in chunks]
            )
            records = [
                VectorRecord(
                    vector_id=chunk.vector_id,
                    content=chunk.content,
                    embedding=embedding,
                    metadata={
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.id,
                        "chunk_index": chunk.chunk_index,
                        "filename": document.filename,
                        "source_location": chunk.source_location,
                        "document_type": document.document_type,
                        "chunk_type": chunk.chunk_type,
                        "section_title": chunk.section_title or "",
                        "source_name": document.source_name or "",
                    },
                )
                for chunk, embedding in zip(chunks, embeddings)
            ]
            vector_store.upsert(records)

            document.status = "completed"
            document.chunk_count = len(chunks)
            document.error_message = None
            db.commit()
            db.refresh(document)
            return document
        except Exception as exc:
            document.status = "failed"
            document.error_message = str(exc)
            db.commit()
            db.refresh(document)
            raise

    def list_documents(self, db: Session) -> List[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._-]", "_", filename)[:120] or "upload.txt"


document_service = DocumentService()
