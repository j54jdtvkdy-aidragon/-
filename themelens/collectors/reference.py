from __future__ import annotations

import feedparser
import httpx

from ..models import Document

UA = {"User-Agent": "themelens/0.1 (research tool)"}


class ArxivCollector:
    name = "arxiv"
    label = "arXiv論文"

    def collect(self, query, limit, lang):
        # arXiv は英語中心。日本語クエリでは当たりにくいので、そのまま投げて結果が無ければ空を返す。
        r = httpx.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": limit, "sortBy": "relevance"},
            headers=UA,
            timeout=30,
        )
        r.raise_for_status()
        feed = feedparser.parse(r.text)
        return [
            Document(self.name, " ".join(e.title.split()), e.link, " ".join(e.summary.split()), e.get("published", ""))
            for e in feed.entries
        ]


class WikipediaCollector:
    name = "wikipedia"
    label = "Wikipedia"

    def collect(self, query, limit, lang):
        api = f"https://{'ja' if lang == 'ja' else 'en'}.wikipedia.org/w/api.php"
        r = httpx.get(
            api,
            params={
                "action": "query", "format": "json", "generator": "search", "gsrsearch": query,
                "gsrlimit": min(limit, 5), "prop": "extracts", "exintro": 1, "explaintext": 1,
                "exlimit": "max", "inprop": "url",
            },
            headers=UA,
            timeout=20,
        )
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        base = api.rsplit("/w/", 1)[0]
        return [
            Document(self.name, p["title"], f"{base}/?curid={p['pageid']}", p.get("extract", ""))
            for p in sorted(pages.values(), key=lambda p: p.get("index", 0))
        ]
