# OneStreamer の仕組みの説明図（2026-11-05）

教授との MTG 資料用。林の手法メモ（全体像・共通の仕組み・A・B）に対応する。AI（Claude）が林の文章をもとに描いた。

| 図 | 中身 | 根拠 |
|---|---|---|
| `01-overview` | 全体像。Qwen3-VL-4B を追加学習 → 指示で A・B のどちらで動くかが決まる | 論文 §5・付録 C.1・付録 D、公式コード |
| `02-control-tokens` | 共通の仕組み。専用トークン 5 つと使う場面、論文の例（図6・図11 の切り出し）、窓がずれて古い部分が見えなくなること | 論文 表5・§3.1・§3.2、公式コード（`caption_video.py`、`shared/inference_fast.py`、`tokenizer.json`） |
| `03-a-record-then-answer` | A。記録づくり → 回答 | 論文 付録 D・付録 E.2、公式コード（`prompts.py`、`local_runner.py`、`configs/streamingbench.json`、`caption_optimized.py`） |
| `04-b-wait-and-respond` | B。待ち受けて答える、Proactive QA と Proactive Interaction、ベンチごとの違い | 論文 表5、公式コード（`shared/inference_fast.py`、`run_script/recipes.py`、`omnimmi/pa_prompt.txt`・`pa.py`、`vispeak/local_runner.py`、`vlmeval/dataset/ovo_timing.py`） |

- 公式コードは 139 の `/mnt/HDD18TB/hayashi/2026_11_hayashi_onestreamer`（`87508dd`）
- 映像の並び・出力の並び・記録の中身は説明用の例
- 作り直すとき: `src/` の `make_*.py` で SVG を作り、`uvx --from cairosvg cairosvg <svg> -o <png>` で PNG にする（`src/` で実行）
- `paper-crops/` は論文 Zeng et al., arXiv 2610.01762（CC BY 4.0）の図6 上段・下段、図11 の 3 段目を 300dpi で切り出したもの。`02-control-tokens.svg` が相対パスで読む
- PNG にするときは `uvx --from cairosvg cairosvg --unsafe "$(pwd)/02-control-tokens.svg" -o 02-control-tokens.png`（切り出し画像を読むため `--unsafe` と絶対パスが要る）
