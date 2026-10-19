from __future__ import annotations

from ..models import Document


class YouTubeCollector:
    """YouTube を検索し、字幕(自動生成含む)を本文として取得する。字幕が無い動画は説明文のみ。"""

    name = "youtube"
    label = "YouTube"
    MAX_CHARS = 8000

    def collect(self, query, limit, lang):
        import yt_dlp
        from youtube_transcript_api import YouTubeTranscriptApi

        opts = {"quiet": True, "extract_flat": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        api = YouTubeTranscriptApi()
        langs = [lang, "en"] if lang != "en" else ["en"]
        docs = []
        for v in info.get("entries", []):
            text = v.get("description") or ""
            try:
                snippets = api.fetch(v["id"], languages=langs)
                text = " ".join(s.text for s in snippets)[: self.MAX_CHARS]
            except Exception:
                pass  # 字幕なし・無効の動画は説明文で代用
            docs.append(
                Document(
                    self.name, v.get("title", ""), f"https://www.youtube.com/watch?v={v['id']}", text,
                    meta={"channel": v.get("channel") or v.get("uploader")},
                )
            )
        return docs
