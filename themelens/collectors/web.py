from __future__ import annotations

from ..models import Document


class WebCollector:
    name = "web"
    label = "Web検索"

    def collect(self, query: str, limit: int, lang: str) -> list[Document]:
        from ddgs import DDGS

        region = "jp-jp" if lang == "ja" else "wt-wt"
        hits = DDGS().text(query, region=region, max_results=limit)
        return [
            Document(self.name, h.get("title", ""), h["href"], h.get("body", ""))
            for h in hits
            if h.get("href")
        ]


class NewsCollector:
    """Google News の RSS (APIキー不要)。"""

    name = "news"
    label = "ニュース"

    def collect(self, query: str, limit: int, lang: str) -> list[Document]:
        from urllib.parse import quote

        import feedparser

        hl, gl, ceid = ("ja", "JP", "JP:ja") if lang == "ja" else ("en", "US", "US:en")
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl={hl}&gl={gl}&ceid={ceid}"
        feed = feedparser.parse(url)
        return [
            Document(
                self.name,
                e.get("title", ""),
                e.get("link", ""),
                e.get("summary", ""),
                e.get("published", ""),
                {"publisher": getattr(e.get("source"), "title", "") if e.get("source") else ""},
            )
            for e in feed.entries[:limit]
            if e.get("link")
        ]
