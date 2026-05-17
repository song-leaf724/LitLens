from typing import Dict, List

import httpx

from app.book_sources.base import BookSearchItem, BookSourceError, BookSourceNotFoundError, DownloadedBook


class WikisourceProvider:
    source_name = "wikisource"
    api_base = "https://zh.wikisource.org/w/api.php"

    async def search(self, query: str, limit: int = 10) -> List[BookSearchItem]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=self._headers()) as client:
                response = await client.get(self.api_base, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise BookSourceError(f"Wikisource 搜索请求失败：{exc}") from exc
        except ValueError as exc:
            raise BookSourceError("Wikisource 搜索结果不是有效 JSON。") from exc

        results = payload.get("query", {}).get("search", [])
        return [
            BookSearchItem(
                source=self.source_name,
                source_id=str(item["pageid"]),
                title=item.get("title") or str(item["pageid"]),
                author=None,
                language="zh",
                source_url=f"https://zh.wikisource.org/wiki/{item.get('title', '').replace(' ', '_')}",
                license="CC BY-SA / public domain depending on source text",
            )
            for item in results
        ]

    async def download(self, source_id: str) -> DownloadedBook:
        params = {
            "action": "query",
            "prop": "extracts|info",
            "explaintext": 1,
            "inprop": "url",
            "pageids": source_id,
            "format": "json",
            "utf8": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=self._headers()) as client:
                response = await client.get(self.api_base, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise BookSourceError(f"Wikisource 下载请求失败：{exc}") from exc
        except ValueError as exc:
            raise BookSourceError("Wikisource 页面内容不是有效 JSON。") from exc

        page = payload.get("query", {}).get("pages", {}).get(str(source_id))
        if not page or "missing" in page:
            raise BookSourceNotFoundError(f"Wikisource 未找到页面：{source_id}")
        text = (page.get("extract") or "").strip()
        if not text:
            raise BookSourceError("下载到的 Wikisource 文本为空。")
        title = page.get("title") or str(source_id)
        return DownloadedBook(
            source=self.source_name,
            source_id=source_id,
            title=title,
            author=None,
            language="zh",
            source_url=page.get("fullurl") or f"https://zh.wikisource.org/wiki/{title.replace(' ', '_')}",
            license="CC BY-SA / public domain depending on source text",
            text=text,
        )

    def _headers(self) -> Dict[str, str]:
        return {"User-Agent": "LitLens/0.1 (public text import)"}
