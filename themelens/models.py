from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Document:
    """収集した1件の情報。媒体を問わず共通形式にそろえる。"""

    source: str  # 収集元の名前 (例: "news", "reddit")
    title: str
    url: str
    text: str = ""  # 本文または要約
    published: str = ""  # ISO8601 など。不明なら空
    meta: dict = field(default_factory=dict)

    def key(self) -> str:
        return self.url.split("#")[0].rstrip("/")
