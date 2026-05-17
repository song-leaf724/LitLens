from sqlalchemy.orm import Session

from app.book_sources.registry import book_source_registry
from app.services.document_service import DocumentIngestMetadata, document_service


class BookImportService:
    async def search(self, source: str, query: str, limit: int = 10):
        provider = book_source_registry.get(source)
        return await provider.search(query=query, limit=limit)

    async def import_book(self, db: Session, source: str, source_id: str):
        provider = book_source_registry.get(source)
        downloaded = await provider.download(source_id)
        filename = self._filename(downloaded.title)
        return await document_service.import_text(
            db=db,
            filename=filename,
            text=downloaded.text,
            metadata=DocumentIngestMetadata(
                title=downloaded.title,
                author=downloaded.author,
                source_name=downloaded.source,
                source_id=downloaded.source_id,
                source_url=downloaded.source_url,
                license=downloaded.license,
            ),
        )

    def _filename(self, title: str) -> str:
        safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in title)
        safe = safe.strip("_")[:120] or "imported_book"
        return f"{safe}.txt"


book_import_service = BookImportService()
