import os
import re
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Chunk, Document
from app.rag.chunker import chunk_text
from app.rag.embeddings import embedding_service
from app.rag.parser import parse_document
from app.rag.vector_store import VectorRecord, vector_store


class DocumentService:
    async def upload_document(
        self, db: Session, filename: str, content: bytes
    ) -> Document:
        text = parse_document(filename, content)
        os.makedirs(settings.upload_dir, exist_ok=True)

        document_id = str(uuid.uuid4())
        safe_name = self._safe_filename(filename)
        storage_path = os.path.join(settings.upload_dir, f"{document_id}_{safe_name}")

        with open(storage_path, "wb") as file:
            file.write(content)

        document = Document(
            id=document_id,
            filename=filename,
            file_type=os.path.splitext(filename)[1].lower().lstrip("."),
            storage_path=storage_path,
            status="processing",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            text_chunks = chunk_text(
                text,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )
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

