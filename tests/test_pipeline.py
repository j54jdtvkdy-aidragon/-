from themelens import pipeline
from themelens.analyze import build_prompt, sources_section
from themelens.cli import parse_args, resolve_instruction
from themelens.models import Document
from themelens.presets import PRESETS


class Fake:
    def __init__(self, name, docs=None, fail=False):
        self.name, self.label, self._docs, self._fail = name, name.upper(), docs or [], fail

    def collect(self, q, limit, lang):
        if self._fail:
            raise RuntimeError("boom")
        return self._docs


def test_collect_all_is_fail_soft_and_dedupes(monkeypatch):
    monkeypatch.setattr(pipeline, "COLLECTORS", {
        "a": Fake("a", [Document("a", "t1", "http://x/1"), Document("a", "t2", "http://x/2/")]),
        "b": Fake("b", fail=True),
        "c": Fake("c", [Document("c", "t3", "http://x/2")]),
    })
    docs = pipeline.collect_all("q", ["a", "b", "c"], 5, "ja")
    assert [d.title for d in docs] == ["t1", "t2"]


def test_fit_budget_interleaves_sources_and_truncates():
    def make():
        return [Document("a", "a", f"u{i}", "x" * 100) for i in range(3)] + [Document("b", "b", "ub", "y" * 100)]

    out = pipeline.fit_budget(make(), per_doc=10, total=10_000)
    assert [d.source for d in out][:2] == ["a", "b"]
    assert all(len(d.text) == 10 for d in out)
    assert len(pipeline.fit_budget(make(), per_doc=100, total=400)) < 4


def test_prompt_and_sources(monkeypatch):
    docs = [Document("news", "見出し", "http://n/1", "本文", "2026-10-01")]
    p = build_prompt("テーマ", "指示", docs)
    assert '<doc id="1">' in p and "指示" in p and "本文" in p
    assert "[見出し](http://n/1)" in sources_section(docs)


def test_instruction_priority(tmp_path):
    assert resolve_instruction(parse_args(["t"])) == PRESETS["report"]
    assert resolve_instruction(parse_args(["t", "-p", "market"])) == PRESETS["market"]
    assert resolve_instruction(parse_args(["t", "-p", "market", "-i", "自由"])) == "自由"
    f = tmp_path / "i.txt"
    f.write_text("ファイル指示", encoding="utf-8")
    assert resolve_instruction(parse_args(["t", "-f", str(f)])) == "ファイル指示"
