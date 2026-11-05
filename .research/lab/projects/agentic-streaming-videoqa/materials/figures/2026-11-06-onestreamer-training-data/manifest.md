# OneStreamer の学習とデータの説明図（2026-11-06）

[学習とデータセット作成のまとめ](../../../papers/2026-11-06-onestreamer-training-and-data-summary.md)を図にしたもの。AI（Claude）が論文をもとに描いた。

| 図 | 中身 | 根拠 |
|---|---|---|
| `01-training` | 学習の 1 例（Proactive QA の正解の系列）、teacher forcing、2 種類の損失 | 論文 §3.3・§5、付録 A.1、表7 |
| `02-pstl` | PSTL の選び方（図4 の例を数え直したもの）と表3 | 論文 §3.3、図4、式1〜3、表3・表5 |
| `03-dataset` | OneStreamer-1M の 4 つの族（件数・Core の割合・制御トークン・図5 との対応） | 論文 表5・表6・表7、付録 B.1 |
| `04-data-pipeline` | 図5 の上下の手順と、既存データの扱い | 論文 §4、図5、付録 B.1〜B.3 |

- 系列・確率の例は説明用。Core の件数は表6 から AI が足した値
- 作り直すとき: `src/` で `python3 make_*.py ../<名前>.svg`、`uvx --from cairosvg cairosvg "$(pwd)/<名前>.svg" -o <名前>.png`
