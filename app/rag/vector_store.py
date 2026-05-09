import json
import logging
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    vector_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]


@dataclass
class VectorHit:
    vector_id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class VectorStore:
    def __init__(self) -> None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self.backend = "fallback"
        self._fallback_path = os.path.join(
            settings.chroma_persist_dir, "fallback_vectors.json"
        )
        self._fallback_records: Dict[str, Dict[str, Any]] = {}
        self._collection = None
        self._init_chroma_or_fallback()

    def _init_chroma_or_fallback(self) -> None:
        try:
            import chromadb  # type: ignore

            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            self._collection = client.get_or_create_collection(
                name=settings.chroma_collection_name
            )
            self.backend = "chroma"
            logger.info("Vector store backend: ChromaDB")
        except Exception as exc:
            logger.warning("ChromaDB unavailable, using JSON vector store: %s", exc)
            self.backend = "fallback"
            self._load_fallback()

    def upsert(self, records: List[VectorRecord]) -> None:
        if not records:
            return
        if self.backend == "chroma" and self._collection is not None:
            self._collection.upsert(
                ids=[record.vector_id for record in records],
                documents=[record.content for record in records],
                embeddings=[record.embedding for record in records],
                metadatas=[record.metadata for record in records],
            )
            return

        for record in records:
            self._fallback_records[record.vector_id] = {
                "content": record.content,
                "embedding": record.embedding,
                "metadata": record.metadata,
            }
        self._save_fallback()

    def query(
        self,
        embedding: List[float],
        top_k: int,
        document_id: Optional[str] = None,
    ) -> List[VectorHit]:
        if self.backend == "chroma" and self._collection is not None:
            where = {"document_id": document_id} if document_id else None
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where=where,
            )
            return self._parse_chroma_results(results)

        hits: List[VectorHit] = []
        for vector_id, record in self._fallback_records.items():
            metadata = record["metadata"]
            if document_id and metadata.get("document_id") != document_id:
                continue
            score = _cosine_similarity(embedding, record["embedding"])
            hits.append(
                VectorHit(
                    vector_id=vector_id,
                    content=record["content"],
                    metadata=metadata,
                    score=score,
                )
            )
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]

    def _parse_chroma_results(self, results: Dict[str, Any]) -> List[VectorHit]:
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        hits: List[VectorHit] = []
        for index, vector_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else 0.0
            score = 1.0 / (1.0 + float(distance))
            hits.append(
                VectorHit(
                    vector_id=vector_id,
                    content=documents[index] if index < len(documents) else "",
                    metadata=metadatas[index] if index < len(metadatas) else {},
                    score=score,
                )
            )
        return hits

    def _load_fallback(self) -> None:
        if not os.path.exists(self._fallback_path):
            self._fallback_records = {}
            return
        with open(self._fallback_path, "r", encoding="utf-8") as file:
            self._fallback_records = json.load(file)

    def _save_fallback(self) -> None:
        with open(self._fallback_path, "w", encoding="utf-8") as file:
            json.dump(self._fallback_records, file, ensure_ascii=False, indent=2)


def _cosine_similarity(left: List[float], right: List[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


vector_store = VectorStore()

