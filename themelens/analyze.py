from __future__ import annotations

import os
from datetime import date

import anthropic

from .collectors import COLLECTORS
from .models import Document
from .presets import SYSTEM

DEFAULT_MODEL = "claude-sonnet-5-5"


def build_prompt(theme: str, instruction: str, docs: list[Document]) -> str:
    blocks = []
    for i, d in enumerate(docs, 1):
        label = COLLECTORS[d.source].label if d.source in COLLECTORS else d.source
        head = f"[{i}] ({label}) {d.title}"
        if d.published:
            head += f" / {d.published}"
        blocks.append(f"<doc id=\"{i}\">\n{head}\nURL: {d.url}\n{d.text}\n</doc>")
    return (
        f"テーマ: {theme}\n本日: {date.today().isoformat()}\n\n"
        f"## 分析の指示\n{instruction}\n\n"
        f"## 資料({len(docs)}件)\n" + "\n\n".join(blocks)
    )


def analyze(theme: str, instruction: str, docs: list[Document], model: str | None = None) -> str:
    client = anthropic.Anthropic()
    with client.messages.stream(
        model=model or os.environ.get("THEMELENS_MODEL", DEFAULT_MODEL),
        max_tokens=8000,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(theme, instruction, docs)}],
    ) as stream:
        return stream.get_final_text()


def sources_section(docs: list[Document]) -> str:
    lines = ["## 出典一覧", ""]
    for i, d in enumerate(docs, 1):
        label = COLLECTORS[d.source].label if d.source in COLLECTORS else d.source
        lines.append(f"{i}. [{d.title or d.url}]({d.url}) — {label}")
    return "\n".join(lines)
