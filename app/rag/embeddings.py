import hashlib
import logging
import math
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if settings.llm_api_key and not settings.llm_use_fake:
            try:
                return await self._embed_with_api(texts)
            except Exception as exc:  # pragma: no cover - depends on external API
                logger.warning("Embedding API failed, using local fallback: %s", exc)
        return [self._fallback_embedding(text) for text in texts]

    async def embed_query(self, text: str) -> List[float]:
        return (await self.embed_texts([text]))[0]

    async def _embed_with_api(self, texts: List[str]) -> List[List[float]]:
        url = f"{settings.llm_base_url.rstrip('/')}/embeddings"
        payload = {"model": settings.embedding_model_name, "input": texts}
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(settings.llm_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()["data"]
        ordered = sorted(data, key=lambda item: item.get("index", 0))
        return [item["embedding"] for item in ordered]

    def _fallback_embedding(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        normalized = text.lower()
        tokens = self._tokens(normalized)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _tokens(self, text: str) -> List[str]:
        words = [part for part in text.replace("\n", " ").split(" ") if part]
        if len(words) >= 4:
            return words
        return [text[index : index + 2] for index in range(max(1, len(text) - 1))]


embedding_service = EmbeddingService()

