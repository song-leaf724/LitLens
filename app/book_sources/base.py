from dataclasses import dataclass
from typing import List, Optional, Protocol


@dataclass
class BookSearchItem:
    source: str
    source_id: str
    title: str
    author: Optional[str] = None
    language: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None


@dataclass
class DownloadedBook:
    source: str
    source_id: str
    title: str
    text: str
    author: Optional[str] = None
    language: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None


class BookSourceProvider(Protocol):
    source_name: str

    async def search(self, query: str, limit: int = 10) -> List[BookSearchItem]:
        ...

    async def download(self, source_id: str) -> DownloadedBook:
        ...


class BookSourceError(RuntimeError):
    pass


class BookSourceNotFoundError(BookSourceError):
    pass
