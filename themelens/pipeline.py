from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

import httpx

from .collectors import COLLECTORS
from .models import Document

log = logging.getLogger("themelens")

# 全文取得が有効なのは、検索結果が「記事への入口」でしかない媒体だけ。
FULLTEXT_SOURCES = {"web", "news", "hatena"}


def collect_all(query: str, sources: list[str], limit: int, lang: str) -> list[Document]:
    """媒体ごとに並列収集する。1媒体が失敗しても他は続行する。"""

    def run(name: str) -> list[Document]:
        try:
            docs = COLLECTORS[name].collect(query, limit, lang)
            log.info("%s: %d件", COLLECTORS[name].label, len(docs))
            return docs
        except Exception as e:  # noqa: BLE001 - 媒体単位で握りつぶして続行する
            log.warning("%s の収集に失敗: %s", COLLECTORS[name].label, e)
            return []

    with ThreadPoolExecutor(max_workers=len(sources)) as ex:
        results = list(ex.map(run, sources))
    return dedupe([d for docs in results for d in docs])


def dedupe(docs: list[Document]) -> list[Document]:
    seen, out = set(), []
    for d in docs:
        if d.key() not in seen:
            seen.add(d.key())
            out.append(d)
    return out


def _fetch_fulltext(doc: Document) -> None:
    import trafilatura

    try:
        r = httpx.get(doc.url, follow_redirects=True, timeout=15, headers={"User-Agent": "Mozilla/5.0 themelens"})
        r.raise_for_status()
        text = trafilatura.extract(r.text, include_comments=False)
        if text and len(text) > len(doc.text):
            doc.text = text
            doc.url = str(r.url)  # Google News のリダイレクトを解決した最終URLにする
    except Exception as e:  # noqa: BLE001
        log.debug("全文取得失敗 %s: %s", doc.url, e)


def enrich(docs: list[Document]) -> None:
    targets = [d for d in docs if d.source in FULLTEXT_SOURCES]
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_fetch_fulltext, targets))


def fit_budget(docs: list[Document], per_doc: int, total: int) -> list[Document]:
    """1件あたりと全体の文字数を制限する。媒体を交互に採用し、特定媒体に偏らないようにする。"""
    by_src: dict[str, list[Document]] = {}
    for d in docs:
        by_src.setdefault(d.source, []).append(d)
    picked, used = [], 0
    while any(by_src.values()):
        for lst in by_src.values():
            if not lst:
                continue
            d = lst.pop(0)
            d.text = d.text[:per_doc]
            cost = len(d.title) + len(d.text) + 50
            if used + cost > total:
                return picked
            picked.append(d)
            used += cost
    return picked
