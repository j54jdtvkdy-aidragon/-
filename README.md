# themelens

テーマを入力すると、Web・ニュース・SNS・学術・動画から情報を集め、Claude が出典付きで分析してMarkdownレポートにするCLI。

## セットアップ
```
pip install -e .
export ANTHROPIC_API_KEY=...
```

## 使い方
```
themelens "生成AIと著作権"                          # 総合レポート(既定)
themelens "生成AIと著作権" -p sentiment             # 世論・反応の分析
themelens "電動キックボード" -p market -s web,news  # 収集元を限定
themelens "半導体規制" -i "賛成派と反対派の論拠を表にして比較して"   # 分析内容を自由指定
themelens "半導体規制" -f my_instruction.txt        # 指示をファイルで渡す
themelens "テーマ" --collect-only                   # 収集結果だけ確認(LLM不使用)
```
プリセット: `report` / `sentiment` / `market` / `factcheck`(`themelens/presets.py`)。

## 収集元(`-s` で指定)
`web` `news` `reddit` `hatena` `arxiv` `wikipedia` `youtube`

新しい媒体は `themelens/collectors/` に `name` / `label` / `collect(query, limit, lang)` を持つクラスを足し、
`collectors/__init__.py` に登録するだけで追加できます。

## 注意
- 失敗した媒体はスキップして続行します。
- X(Twitter)など有料APIが必要な媒体は未対応です。
- SNS投稿は意見として扱うようプロンプトで指示しています。各サイトの利用規約・robots に従って利用してください。
