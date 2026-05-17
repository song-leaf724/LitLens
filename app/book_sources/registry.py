from typing import Dict

from app.book_sources.base import BookSourceProvider
from app.book_sources.gutenberg import GutenbergProvider
from app.book_sources.wikisource import WikisourceProvider


class BookSourceRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, BookSourceProvider] = {}
        self.register(GutenbergProvider())
        self.register(WikisourceProvider())

    def register(self, provider: BookSourceProvider) -> None:
        self._providers[provider.source_name] = provider

    def get(self, source: str) -> BookSourceProvider:
        normalized = source.strip().lower()
        if normalized not in self._providers:
            available = ", ".join(sorted(self._providers))
            raise KeyError(f"未知书源：{source}。可用书源：{available}")
        return self._providers[normalized]


book_source_registry = BookSourceRegistry()
