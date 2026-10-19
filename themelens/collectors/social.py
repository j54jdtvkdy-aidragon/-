from __future__ import annotations

from datetime import datetime, timezone

import feedparser
import httpx

UA = {"User-Agent": "themelens/0.1 (research tool)"}


class RedditCollector:
    name = "reddit"
    label = "Reddit"

    def collect(self, query, limit, lang):
        from ..models import Document

        r = httpx.get(
            "https://www.reddit.com/search.json",
            params={"q": query, "limit": limit, "sort": "relevance", "t": "year"},
            headers=UA,
            timeout=20,
        )
        r.raise_for_status()
        docs = []
        for c in r.json()["data"]["children"]:
            d = c["data"]
            published = datetime.fromtimestamp(d["created_utc"], timezone.utc).isoformat()
            docs.append(
                Document(
                    self.name,
                    d["title"],
                    "https://www.reddit.com" + d["permalink"],
                    d.get("selftext", "")[:3000],
                    published,
                    {"score": d.get("score"), "comments": d.get("num_comments"), "subreddit": d.get("subreddit")},
                )
            )
        return docs


class HatenaCollector:
    """はてなブックマークの検索RSS。日本語圏の反応を見る用。"""

    name = "hatena"
    label = "はてなブックマーク"

    def collect(self, query, limit, lang):
        from urllib.parse import quote

        from ..models import Document

        url = f"https://b.hatena.ne.jp/search/text?q={quote(query)}&mode=rss&sort=popular"
        feed = feedparser.parse(url)
        return [
            Document(self.name, e.get("title", ""), e.get("link", ""), e.get("summary", ""), e.get("published", ""))
            for e in feed.entries[:limit]
            if e.get("link")
        ]
