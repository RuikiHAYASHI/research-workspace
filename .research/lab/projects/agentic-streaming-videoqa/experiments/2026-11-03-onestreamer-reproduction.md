---
date: 2026-11-03
project: agentic-streaming-videoqa
topic: OneStreamer-4B の論文 Table 1 を、公式コードと同じ設定で 139 で再現する（実行ログ）
status: running
tags: [onestreamer, reproduction, odv-bench, ovo-bench, vispeak]
---

# OneStreamer-4B の再現（実行ログ、2026-11-03〜）

- 計画: [再現計画](../specs/2026-11-02-onestreamer-reproduction-plan-spec.md)
- 書いた人: AI（Claude）。林は 2026-11-03 01:4x に「GPU 0〜3 を使って再現性のある実験をし、GitHub の流れなどをしっかり記録して」と依頼した。条件と結果のまとめは林が 11/04 以降に行う
- 数値はすべて機械の出力（`judge_outputs/.../metrics.json`）から写したもの。AI の解釈は「AI の考え」と書く

## 1. GitHub とコードの流れ

```text
MCG-NJU/OneStreamer (公式, Apache-2.0)          … upstream（読むだけ。push は DISABLED に設定）
   └─ 338e5fe  docs: announce OneStreamer-Core source videos   ← 2026-11-03 時点の公式の最新
        │  clone（fork ではない）
        ▼
RuikiHAYASHI/2026_11_hayashi_onestreamer (private, 林が 11/03 に空で作成)   … origin
   ├─ main          = 338e5fe（公式そのまま。触らない）
   └─ repro/table1  = 338e5fe + 再現用の commit
        ├─ 37ad913  repro: paths.json と models.json を 139 のデータ・重みの場所に向ける
        ├─ d198406  repro: GPU 枚数を指定して公式の評価キューを呼ぶ起動スクリプトを追加（repro/run.sh）
        └─ 86ab953  repro: ベンチを順に smoke → full で回すキューを追加（repro/queue.sh）
```

- 139 の作業場所: `/mnt/HDD18TB/hayashi/2026_11_hayashi_onestreamer`（ブランチ `repro/table1`）
- fork にしなかった理由: 公開リポジトリの fork は private にできない。空の private リポジトリに公式の履歴ごと push した。公式の更新は `git fetch upstream` で取れる
- 公式の `Eval/` の中で変えたのは `Eval/run_script/configs/paths.json` と `models.json` だけ。推論・採点のコード、`recipes.py`、`Proactive_Eval/OneStreamer/configs/*.json` は公式のまま
  - `repro/run.sh` は `Eval/` の外に置いた。公式がコードの同一性として記録する `code_fingerprint`（`Eval/` 直下と `VLMEvalKit/`・`Proactive_Eval/`・`run_script/` の .py/.sh/.txt と configs）には、`paths.json`・`models.json` の書き換えだけが入る
- `LICENSE`・`NOTICE` は残している。データと重みはリポジトリに入れない（出力の `Eval/outputs/`・`Eval/judge_outputs/` は公式の `.gitignore` で追跡外）
- 前回の試行の clone（`2026_10_public_text_memory_baselines/OneStreamer`、`lvb/` の追加と `engine.py` の修正あり）は使っていない。重みだけ再利用した（下記）

## 2. 環境（139）

- GPU: RTX A6000 48GB × 4（林の許可で 0〜3 を使う、2026-11-03 01:4x）。ドライバ 615.71.09、カーネル 7.0.0-38
- Python 環境: `/mnt/HDD18TB/hayashi/envs/onestreamer-eval`（139 に conda がないため uv で Python 3.10.9 を用意し、中は公式 `Eval/README.md` と同じ pip の手順）
  - 作り方: `/mnt/HDD18TB/hayashi/envs/setup_onestreamer_eval.sh`、ログ: 同 `setup_onestreamer_eval.log`、全パッケージ: 同 `onestreamer-eval.freeze.txt`
  - torch 2.6.0+cu124、torchvision 0.21.0+cu124、cuDNN 9.1（90100）、flash-attn 2.7.4.post1、Transformers 4.57.6、OpenCV 4.13.0.92（`--no-deps`）、NumPy 1.26.4、Decord 0.6.0、PyAV 14.2.0、qwen-vl-utils 0.0.14、accelerate 1.12.0 — 公式 `Eval/docs/environment.md` の値とすべて一致
  - 公式との違い: flash-attn は 139 に nvcc がないため、ソースからビルドせず、公式リリースのビルド済み wheel（`cu12torch2.6cxx11abiFALSE-cp310`）を入れた。公式は「PyTorch の wheel は cxx11abiFALSE」としており、それに合う版
  - `pip check` の警告は2件で、どちらも公式が「既知の例外」とするもの（OpenCV の NumPy>=2 宣言、Decord のプラットフォーム表記）
- 重み:
  - OneStreamer-4B: `/mnt/HDD18TB/hayashi/2026_10_public_text_memory_baselines/models/OneStreamer-4B`（10/27 に落としたもの）。HF のダウンロード記録 16 ファイルすべてが `MCG-NJU/OneStreamer-4B@fba29e66908b424877951fa8de46459537c8aa23` で、重み4ファイルの大きさも HF と一致
  - Qwen3-VL-4B-Instruct（no special token）: `/mnt/HDD18TB/hayashi/data/models/Qwen3-VL-4B-Instruct_no_special_token`、`Qwen/Qwen3-VL-4B-Instruct@ebb281ec70b05090aa6165b016eac8ec08e71b17` を 11/03 に落とし直した（前回の分は入手元の記録がなく、`video_preprocessor_config.json` などが欠けていた）。special token は足していない

## 3. データ（139 の `/mnt/HDD18TB/hayashi/data/<公式の名前>/`）

- 置き場所は林の判断（11/03）。zip・tar は展開と動画の確認が済んだものから消す（林の判断）
- HF の版は 11/03 の sha に固定してダウンロードした（記録: `/mnt/HDD18TB/hayashi/data/_onestreamer_download/revisions_2026-11-03.txt`、スクリプトとログも同じ場所）

| 公式の名前 | HF（revision） | 置き方 | 状態 |
|---|---|---|---|
| ODVBench | `MCG-NJU/ODV-Bench@5dcf37c` | zip ごとに `TOI_Recognition/`・`TR_Analysis/`・`TS_Retrieval/` へ展開（zip の中にタスク名のフォルダがないため） | 注釈の 1,190 本すべてあり、OpenCV で開けた。zip 削除済み |
| ViSpeak-Bench | `fushh7/ViSpeak-Bench@4357ec8` | zip の中の `ViSpeak-Bench/` を `data/` に展開（ルート直下にタスクのフォルダ） | 700 本すべて開けた。zip 削除済み |
| OVOBench | `JoeLeelyf/OVO-Bench@fec29e3` | tar のまま `chunked_videos/`（3,035本）・`src_videos/`（645本）に展開 | OVO-Timing の 172 本（すべて chunked_videos）が開けた。展開の大きさが tar と一致し、tar 削除済み（chunked の tar は 143 にもある）。QA 用の TSV は未入手 |
| ProactiveVideoQA | `wangyueqian/ProactiveVideoQA@7f59bce` | `<EGO/TV/VAD/WEB>/anno.json`（HF からコピー）と、`videos.zip` を各フォルダに展開した `videos/` | 1,377 本すべて開けた。zip の件数と一致し、zip 削除済み |
| OmniMMI | `bigai-nlco/OmniMMI@7024889` | 5タスクの JSON と `videos/` だけを落とす | ダウンロード中 |
| StreamingBench | `mjuicem/StreamingBench@48872fa` | — | ダウンロード待ち（`StreamingBench.tsv` がないので回せない） |
| OVBench | `MCG-NJU/OVBench@4d9ddfa` | 公式は `OVBench/<注釈の video_id>` を探す。フレーム画像の zip（AVA・ArgoVerse・BDD・Charades・HACS・LaSOT・YFCC100M）はトップのフォルダがないので `OVBench/<名前>/` へ。`coin/`→`COIN/`、`HiREST/`→`hirest/` に名前だけ変えた（注釈の大文字・小文字に合わせる）。`AVA_RAW/` は `OVBench_new/AVA_RAW/`（`extract_ovbench.sh`） | 展開中。New AVA の JSON がないので回せない |

### 計画（spec）と違ったこと

1. **OmniMMI の動画は `clips/` ではなく `videos/`**。公式は `OmniMMI/videos/<video>` を読み、5タスクの注釈が参照する 921 本はすべて HF の `videos/` にあった（`clips/` にあるのは 2 本だけ）
2. **OVBench は TSV が要らなくても今は回せない**。公式の `ovbench_new.py` は `OVBench_new/ovbench_ava_raw_bbox1000.json` がないと `FileNotFoundError` で止まる（New AVA 以外の行も含めて）
3. **公式の入口 `run_eval_8gpu.sh` は GPU 8 枚が必須**（`--require-eight`）。139 は 4 枚なので、同じ `eval_queue.py` を `--gpus 0,1,2,3` で呼ぶ（`repro/run.sh`）。GPU 枚数で変わるのは問題を GPU に割り振る分け方（shard）だけで、各問題の入力・設定・seed は同じ（AI の読み: `recipes.partitions` は問題の一覧を負荷で分けるだけ）。ただし、バッチや並びが違うことによる GPU の数値のわずかな差は否定できない
4. **OVO-Timing に src_videos は要らなかった**。公式のコードはまず `chunked_videos/<id>.mp4`（`<id>_<k>.mp4`）を探し、なければ `OVOBench/<注釈の video>` を探す。dry-run では 172 問すべてが `chunked_videos/` に見つかった。OVO-Timing は 1,640 件の注釈のうち Forward の3タスク（REC 82・CRR 48・SSR 42）だけを使う
5. **OVO-Timing だけはサンプリングで答えを作る**（公式の `recipes.protocol`: `temperature=0.7, top_p=0.8, top_k=20, seed=42`）。ほかのベンチは貪欲デコード（`temperature=0`）。seed は固定だが、GPU の割り振りが公式（8枚）と違うと乱数の進み方が変わる可能性がある（AI の考え。未確認）

## 4. 実行の手順

```bash
cd /mnt/HDD18TB/hayashi/2026_11_hayashi_onestreamer
GPUS=0,1,2,3 repro/run.sh <bench> dry    # GPU を使わない。件数・動画の存在を確認（run-id: repro-dry）
GPUS=0,1,2,3 repro/run.sh <bench> smoke  # 各ジョブ1問（--limit 1, run-id: repro-smoke）
GPUS=0,1,2,3 repro/run.sh <bench> full   # 全問（run-id: repro-full）。止まったら同じコマンドで --resume
```

- 推論は `--mode infer`。judge の要らないベンチはそのまま採点まで進む。judge（Qwen3-235B の API）が要るもの（ProactiveVideoQA・OmniMMI の QA・ViSpeak）は、推論の予測だけ保存して採点は保留
- 動画の確認: dry-run の `manifest.json` が持つ「公式が実際に読む動画のパス」を、評価環境の OpenCV 4.13 で開き、先頭と末尾付近の1枚を読む（`/mnt/HDD18TB/hayashi/data/_onestreamer_download/check_media.py`、結果は `Eval/outputs/OneStreamer-4B/<bench>/repro-dry/media_check.json`）
- 出力の場所: 予測 `Eval/outputs/OneStreamer-4B/<bench>/<run-id>/<profile>/<task>/`（`manifest.json` に設定・コード・重み・注釈・動画の fingerprint）、採点 `Eval/judge_outputs/...`（`metrics.json`）、起動ログ `Eval/outputs/_launcher_logs/`

## 5. 状況と結果

論文の値は [Streaming モデルの精度比較](../papers/2026-11-02-streaming-model-benchmark-comparison.md) から（OneStreamer-4B / 基盤の Qwen3-VL-4B）。

| ベンチ | ジョブ・問題数（dry-run） | 動画の確認 | smoke | full | 再現の値 | 論文の値 |
|---|---|---|---|---|---|---|
| ODV-Bench | 1・6,348 | 1,190 本 OK | 通った（11/03 01:44〜01:51） | 実行中（11/03 01:52〜、4 GPU で約4時間の見込み） | — | 71.3 / 57.6 |
| ViSpeak | 6・700 | 700 本 OK | キュー待ち | キュー待ち | 採点保留 | — |
| OVO-Timing | 1・172 | 172 本 OK | キュー待ち | キュー待ち | — | — |
| ProactiveVideoQA | 4・1,427（EGO 326・TV 500・VAD 101・WEB 500） | 1,377 本 OK | キュー待ち | キュー待ち | 採点保留 | — |

## 6. 時系列

- 11/03 00:52 第1弾のダウンロード開始（ODV → OVO → OVBench）。01:19 第2弾（ViSpeak → ProactiveVideoQA → OmniMMI → StreamingBench）を並行で開始
- 11/03 01:12 林の非公開リポジトリへ push（`main`, `repro/table1`）、`37ad913`
- 11/03 01:28 評価環境ができた。ODV-Bench の dry-run と動画の確認が通り、zip を削除。`d198406`（`repro/run.sh`）を push。ViSpeak も同様
- 11/03 01:4x 林から GPU 0〜3 の許可。01:44 ODV-Bench の smoke（1問）を開始し、01:51 に推論〜採点まで通った（重みの読み込みに約1分半。予測は不正解だが 1 問なので意味はない）。01:52 full を開始
- 11/03 02:31 ProactiveVideoQA の展開・dry-run・動画の確認が済み、zip を削除
- 11/03 02:33 第1弾のダウンロード（OVBench まで）が終わった。02:36 OVO-Bench の展開が終わり、OVO-Timing の dry-run と動画の確認が済んだ。tar を削除
- 11/03 02:4x OVBench の展開を開始。ODV-Bench の full は 02:48 時点で 3,161 / 6,348 問（エラーなし）
- 11/03 02:48 `repro/queue.sh` で、ODV-Bench の full が終わったら OVO-Timing → ViSpeak → ProactiveVideoQA を順に smoke → full で回すキューを開始（tmux `os-queue1`、ログ `Eval/outputs/_launcher_logs/queue1.log`）

## 7. 報告ページと論文解説スライド（2026-11-03 林の依頼）

- 報告ページ（HTML の Artifact、非公開）: https://claude.ai/artifact/NE8jaHtDzUGo1k7cFsaxQ9
  - ベンチごとに、再現の値と論文の値、サブタスクごとの正答率、選択肢ごとの予測と正解の割合、具体例（サブタスクごとに正解 2・不正解 2、入力区間の画像 8 枚と最大 30 秒の動画、AI の考察）を載せる
  - 生成: `repro/report/build_report.py`、例の固定: `repro/report/selection.json`、考察: `repro/report/notes.json`（AI が画像を見て書いたもの。未検証）
  - 林の指示（11/03 03:xx）: トークン節約のため、更新はベンチが1つ終わるごとに行う。うまくいった例・いかなかった例を複数残す
- 論文解説スライド（Slides の Artifact、74 枚、Appendix A〜F と公式コードとの対応を含む）: https://claude.ai/artifact/71xwDrvZMduRQkKHxxvakv
  - 別のエージェントが作成。表の多いスライドは文字がはみ出している可能性あり（描画は未確認）

### スライド作成のときに公式コードで確かめたこと（再現に関わるもの。AI が読んだ結果）

- 記憶づくり（OVO-Bench・StreamingBench）は 4fps・1 秒ごとの更新で、文脈は 128 枚 = 32 秒に切り詰める。32 秒より古い映像と自分の記録は、記憶づくりの最中は見えない（`src/onestreamer/caption_video.py`）
- 回答は「記憶 + 直近 16 枚（1fps、元の解像度）」、記憶が 12,000 token を超えたときだけ選別する（`src/onestreamer/memory.py`）
- OVO-Timing だけ温度 0.7・top_p 0.8・top_k 20 のサンプリング（seed 42）。論文には書かれていない
- ViSpeak の採点は、公式ドキュメントでは「±2 秒」だが、コードは [正解の時刻, +2 秒] で、早すぎる応答を正解にしない（`Proactive_Eval/ViSpeak-Bench/src/vispeak/scoring.py`）
- 判定 LLM は Qwen3-235B-A22B（DashScope、温度 0、`configs/judge.json`）。学習コード（PSTL）は公開されておらず、再現できるのは評価まで
