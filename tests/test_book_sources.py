from fastapi.testclient import TestClient

from app.book_sources.base import BookSearchItem, DownloadedBook
from app.book_sources.registry import book_source_registry
from app.main import app


class FakeProvider:
    source_name = "fake"

    async def search(self, query: str, limit: int = 10):
        return [
            BookSearchItem(
                source=self.source_name,
                source_id="fake-1",
                title="Fake Book",
                author="Tester",
                language="zh",
                source_url="https://example.test/fake-1",
                license="Public domain",
            )
        ]

    async def download(self, source_id: str):
        return DownloadedBook(
            source=self.source_name,
            source_id=source_id,
            title="静夜思",
            author="李白",
            language="zh",
            source_url="https://example.test/fake-1",
            license="Public domain",
            text="床前明月光\n疑是地上霜\n举头望明月\n低头思故乡",
        )


def test_book_source_search_and_import_with_fake_provider() -> None:
    book_source_registry.register(FakeProvider())

    with TestClient(app) as client:
        search_response = client.get("/book-sources/search", params={"source": "fake", "q": "静夜思"})
        assert search_response.status_code == 200
        assert search_response.json()["results"][0]["title"] == "Fake Book"

        import_response = client.post(
            "/book-sources/import",
            json={"source": "fake", "source_id": "fake-1"},
        )
        assert import_response.status_code == 200
        document = import_response.json()["document"]
        assert document["title"] == "静夜思"
        assert document["author"] == "李白"
        assert document["source_name"] == "fake"
        assert document["document_type"] == "classical_poetry"
        assert document["chunk_count"] >= 2


def test_unknown_book_source_returns_400() -> None:
    with TestClient(app) as client:
        response = client.get("/book-sources/search", params={"source": "missing", "q": "x"})

    assert response.status_code == 400
