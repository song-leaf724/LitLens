import re
from typing import Dict, List, Optional

import httpx

from app.book_sources.base import BookSearchItem, BookSourceError, BookSourceNotFoundError, DownloadedBook
from app.book_sources.http_client import async_client_options


class GutenbergProvider:
    source_name = "gutenberg"
    api_base = "https://gutendex.com/books/"

    async def search(self, query: str, limit: int = 10) -> List[BookSearchItem]:
        params = {"search": query}
        try:
            async with httpx.AsyncClient(**async_client_options(20.0, self._headers())) as client:
                response = await client.get(self.api_base, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise BookSourceError(f"Gutendex 搜索请求失败：{exc}") from exc
        except ValueError as exc:
            raise BookSourceError("Gutendex 搜索结果不是有效 JSON。") from exc

        items: List[BookSearchItem] = []
        for item in payload.get("results", [])[:limit]:
            source_id = str(item.get("id"))
            title = item.get("title") or f"Gutenberg {source_id}"
            authors = item.get("authors") or []
            author = ", ".join(author.get("name", "") for author in authors if author.get("name")) or None
            languages = item.get("languages") or []
            items.append(
                BookSearchItem(
                    source=self.source_name,
                    source_id=source_id,
                    title=title,
                    author=author,
                    language=languages[0] if languages else None,
                    source_url=f"https://www.gutenberg.org/ebooks/{source_id}",
                    license="Public domain",
                )
            )
        return items

    async def download(self, source_id: str) -> DownloadedBook:
        try:
            async with httpx.AsyncClient(**async_client_options(30.0, self._headers())) as client:
                detail_response = await client.get(f"{self.api_base}/{source_id}")
                if detail_response.status_code == 404:
                    raise BookSourceNotFoundError(f"Project Gutenberg 未找到作品：{source_id}")
                detail_response.raise_for_status()
                detail = detail_response.json()

                text_url = self._select_text_url(detail.get("formats") or {})
                if not text_url:
                    raise BookSourceError("该 Gutenberg 作品没有可用 plain text 格式。")
                text_response = await client.get(text_url)
                text_response.raise_for_status()
        except BookSourceError:
            raise
        except httpx.HTTPError as exc:
            raise BookSourceError(f"Gutenberg 下载请求失败：{exc}") from exc
        except ValueError as exc:
            raise BookSourceError("Gutenberg 作品详情不是有效 JSON。") from exc

        title = detail.get("title") or f"Gutenberg {source_id}"
        authors = detail.get("authors") or []
        author = ", ".join(author.get("name", "") for author in authors if author.get("name")) or None
        languages = detail.get("languages") or []
        text = self._clean_gutenberg_text(text_response.text)
        if not text.strip():
            raise BookSourceError("下载到的 Gutenberg 文本为空。")
        return DownloadedBook(
            source=self.source_name,
            source_id=source_id,
            title=title,
            author=author,
            language=languages[0] if languages else None,
            source_url=f"https://www.gutenberg.org/ebooks/{source_id}",
            license="Public domain",
            text=text,
        )

    def _select_text_url(self, formats: Dict[str, str]) -> Optional[str]:
        preferred = [
            "text/plain; charset=utf-8",
            "text/plain; charset=us-ascii",
            "text/plain",
        ]
        for key in preferred:
            value = formats.get(key)
            if value and not value.endswith(".zip"):
                return value
        for key, value in formats.items():
            if key.startswith("text/plain") and value and not value.endswith(".zip"):
                return value
        return None

    def _clean_gutenberg_text(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        start_match = re.search(r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*", normalized, re.I | re.S)
        end_match = re.search(r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*", normalized, re.I | re.S)
        if start_match:
            normalized = normalized[start_match.end():]
        if end_match:
            normalized = normalized[:end_match.start()]
        return normalized.strip()

    def _headers(self) -> Dict[str, str]:
        return {"User-Agent": "LitLens/0.1 (public-domain text import)"}
