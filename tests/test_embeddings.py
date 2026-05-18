import pytest

from app.rag.embeddings import EmbeddingService


@pytest.mark.anyio
async def test_embedding_api_batches_requests(monkeypatch) -> None:
    service = EmbeddingService(dimension=4)
    calls = []

    monkeypatch.setattr("app.rag.embeddings.settings.embedding_batch_size", 2)

    async def fake_embed_batch(texts):
        calls.append(list(texts))
        return [[float(len(text))] * 4 for text in texts]

    monkeypatch.setattr(service, "_embed_batch_with_api", fake_embed_batch)

    result = await service._embed_with_api(["a", "bb", "ccc", "dddd", "eeeee"])

    assert calls == [["a", "bb"], ["ccc", "dddd"], ["eeeee"]]
    assert result == [[1.0] * 4, [2.0] * 4, [3.0] * 4, [4.0] * 4, [5.0] * 4]
