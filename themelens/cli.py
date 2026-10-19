from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from .analyze import analyze, sources_section
from .collectors import COLLECTORS, DEFAULT_SOURCES
from .pipeline import collect_all, enrich, fit_budget
from .presets import PRESETS


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="themelens", description="テーマを多媒体から収集して自動分析する")
    p.add_argument("theme", help="分析したいテーマ (例: 生成AIと著作権)")
    p.add_argument("-p", "--preset", choices=PRESETS, default="report", help="分析プリセット (既定: report)")
    p.add_argument("-i", "--instruction", help="分析内容を自由に指定 (プリセットより優先)")
    p.add_argument("-f", "--instruction-file", type=Path, help="分析指示を書いたファイル")
    p.add_argument("-s", "--sources", default=",".join(DEFAULT_SOURCES), help=f"収集元をカンマ区切りで指定: {','.join(COLLECTORS)}")
    p.add_argument("-n", "--limit", type=int, default=8, help="媒体ごとの最大取得件数 (既定: 8)")
    p.add_argument("--lang", choices=["ja", "en"], default="ja", help="検索言語 (既定: ja)")
    p.add_argument("--max-chars", type=int, default=150_000, help="LLMへ渡す資料の総文字数上限")
    p.add_argument("-o", "--output", type=Path, help="出力先 (既定: reports/<日時>_<テーマ>.md)")
    p.add_argument("--model", help="使用モデル (環境変数 THEMELENS_MODEL でも指定可)")
    p.add_argument("--collect-only", action="store_true", help="収集だけ行い、収集結果の一覧を表示して終了")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def resolve_instruction(args) -> str:
    if args.instruction_file:
        return args.instruction_file.read_text(encoding="utf-8")
    return args.instruction or PRESETS[args.preset]


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in sources if s not in COLLECTORS]
    if unknown:
        print(f"不明な収集元: {', '.join(unknown)} (使用可能: {', '.join(COLLECTORS)})", file=sys.stderr)
        return 2

    docs = collect_all(args.theme, sources, args.limit, args.lang)
    if not docs:
        print("資料が1件も集まりませんでした。ネットワークやテーマの表現を確認してください。", file=sys.stderr)
        return 1
    logging.info("全文取得中 ...")
    enrich(docs)
    docs = fit_budget(docs, per_doc=6000, total=args.max_chars)

    if args.collect_only:
        for i, d in enumerate(docs, 1):
            print(f"[{i}] ({d.source}) {d.title}\n    {d.url}")
        return 0

    logging.info("%d件の資料を分析中 ...", len(docs))
    body = analyze(args.theme, resolve_instruction(args), docs, args.model)
    report = f"# {args.theme}\n\n{body}\n\n{sources_section(docs)}\n"

    out = args.output
    if not out:
        slug = re.sub(r"[^\w\-]+", "_", args.theme)[:40]
        out = Path("reports") / f"{datetime.now():%Y%m%d_%H%M}_{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    logging.info("保存しました: %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
