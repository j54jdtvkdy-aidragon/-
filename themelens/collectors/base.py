from __future__ import annotations

from typing import Protocol

from ..models import Document


class Collector(Protocol):
    name: str
    label: str  # CLI/レポートでの表示名

    def collect(self, query: str, limit: int, lang: str) -> list[Document]: ...
