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
| OmniMMI | `bigai-nlco/OmniMMI@7024889` | 5タスクの JSON と `videos/` だけを落とした（`--include`） | 9 ジョブ・2,200 問、921 本すべて開けた |
| StreamingBench | `mjuicem/StreamingBench@48872fa` | zip のまま `_archives/` に置く。中は `sample_N/video.mp4` で、カテゴリ間で名前が重なる可能性があり、置き方は `StreamingBench.tsv` の `video` 列を見ないと決められない | ダウンロード済み・未展開（TSV がないので回せない） |
| OVBench | `MCG-NJU/OVBench@4d9ddfa` | 公式は `OVBench/<注釈の video_id>` を探す。フレーム画像の zip（AVA・ArgoVerse・BDD・Charades・HACS・LaSOT・YFCC100M）はトップのフォルダがないので `OVBench/<名前>/` へ。`coin/`→`COIN/`、`HiREST/`→`hirest/` に名前だけ変えた（注釈の大文字・小文字に合わせる）。`AVA_RAW/` は `OVBench_new/AVA_RAW/`（`extract_ovbench.sh`） | 展開済み。New AVA 以外の 5,694 行が指す動画・画像フォルダはすべてあった。zip の件数と展開した件数が一致し、zip 削除済み。New AVA の JSON がないので回せない |

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
| ODV-Bench | 1・6,348 | 1,190 本 OK | 通った（11/03 01:44〜01:51） | 完了（11/03 01:52〜03:51、約2時間） | **71.36**（公式の採点、選択肢を読めなかった予測 0） | 71.3 / 57.6 |
| ViSpeak | 6・800 問（動画 700 本） | 700 本 OK | 通った（11/03 05:12〜05:13） | 完了（11/03 05:13〜05:25、約12分） | judge（0〜5 点）は保留。公式の `response_is_in_time` での時刻の判定は 6 タスク平均 74.9%（点の上限 3.75） | 2.87 / 2.41（judge の点） |
| OVO-Timing | 1・172 | 172 本 OK | 通った（11/03 03:52〜03:55） | 完了（11/03 03:55〜05:12、約1時間20分） | **42.9**（平均 F1、±2 秒。CRR 25.2・REC 63.1・SSR 40.5。公式の採点） | 41.6 / 29.4 |
| ProactiveVideoQA | 4・1,427（EGO 326・TV 500・VAD 101・WEB 500） | 1,377 本 OK | 通った（11/03 05:25〜05:42） | 一時停止（11/03 05:42〜10:41、EGO 76/326 まで。judge が要るので、林の指示で作り直した 3 ベンチのあとに resume） | judge は回さない（§8.2） | 48.7 / 34.3（judge の点） |
| OmniMMI | 9・2,200（PA 200 と、AP・SI・MD・SG を ASR あり・なしで） | 921 本 OK | 作り直した 3 ベンチのあと | — | PA だけローカルで採点。ほかは judge で、回さない（§8.2） | 36.6 / 29.4（5 タスクの平均） |
| OVO-Bench（QA） | 2・3,035（memory・recent16） | 3,035 本 OK | **作り直した注釈**で、StreamingBench のあと。Backward（631）→ Real-Time（837）→ Forward（1,567）の順に分けて回す（§8.1） | — | — | 72.1 / 58.8（Real-Time 81.4・Backward 77.9・Forward 56.9） |
| StreamingBench Real-Time | 1・2,500 | 499 本を展開済み（11/03 10:49） | **作り直した注釈**で、いちばん先。1 回目（11:06〜）は注釈の時刻の書き間違いで 14:28 に止まり（281/2,500 済）、`recon2`（14:34〜）は壊れた配布動画 sample_332 で 11/04 03:43 に止まった（1,095 済）。recon2 で済んだ 1,092 問はそのまま使い、残りの 1,408 問を `recon3` で 11/04 04:57 から回し中（§6） | — | — | 86.9 / 81.8 |
| OVBench | 1・6,810（New AVA 以外 5,414・New AVA 1,396） | 5,414 問ぶん OK・AVA_RAW 64 本 | New AVA だけ**作り直した注釈**で、StreamingBench のあと（§8.1） | — | — | 66.8 / 55.4 |

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
- 11/03 03:51 ODV-Bench の full が終わった。正答率 71.36（`Eval/judge_outputs/OneStreamer-4B/odvbench/repro-full/paper/odvbench/metrics.json`）で、論文の 71.3 とほぼ一致。2 択の Distance Prediction（正答率 64.7）は「近づいている」に、Risk Prediction（51.3）は「危険あり」に大きく偏っている（詳しくは報告ページ）。03:52 キューが OVO-Timing の smoke を開始。報告ページを更新（repro `bae1976`）
- 11/03 04:04 データのダウンロードがすべて終わった。OVBench の展開と確認が済み、zip を削除。StreamingBench は置き方が決められないため未展開。OVO-Timing の smoke が通り、03:55 から full
- 11/03 05:12 OVO-Timing の full が終わった。平均 F1 42.9（`Eval/judge_outputs/OneStreamer-4B/ovo_timing/repro-full/paper/ovo_timing/metrics.json`）で、論文の 41.6 より 1.3 高い（サンプリングで応答を作るので多少は揺れうる）。どのタスクも再現率が適合率より高く、応答を多めに出している。CRR では最初の応答が正解より 2 秒以上早いのが 48 問中 29 問。公式の採点は応答の時刻だけを見て中身を見ない（`ovo_timing.py` の `_f1_stats`）。05:12 キューが ViSpeak の smoke を開始し、05:13 から full。報告ページに OVO-Timing のタイムラインと具体例 18 問を追加（repro `1a0b440`）
- 11/03 05:25 ViSpeak の full が終わった（全 800 問）。中身の採点（judge）は保留。時刻の判定だけ公式の関数で数えると 6 タスク平均 74.9%（Gesture 98.5・Termination 99.0・Wake-Up 89.0・Interruption 78.0・Anomaly 45.0・Humor 40.0）。Anomaly と Humor は最後まで応答しない問題が多い（52/200、55/100）。Wake-Up の外れ 11 問はすべて 1 秒目の早すぎる応答。05:25 キューが ProactiveVideoQA の smoke を開始。報告ページに ViSpeak の節を追加（repro `b75b97e`）
- 11/03 10:20〜10:35 林の方針（judge で費用がかかるものより、注釈を作り直して回せるものを優先）で、OVO-Bench・StreamingBench・OVBench（New AVA）の注釈を元の公開注釈から作り直した（§8.1）。ブランチ `repro/reconstructed`（worktree `/mnt/HDD18TB/hayashi/2026_11_hayashi_onestreamer_recon`、`e7801e0`・`6da4035`・`a34bfe7`）。dry-run は OVO-Bench 3,035/3,035（2 設定）・OVBench 6,810/6,810 が通った。tmux `os-queue3`（`repro/reconstruct/queue_recon.sh`）が、ProactiveVideoQA の full が終わったら OmniMMI を止め、OVO-Bench → StreamingBench → OVBench（run-id `recon-*`）→ OmniMMI の順に回す

## 8. 注釈を作り直したベンチと、judge を回さないベンチ（2026-11-03、林への報告用）

### 8.1 注釈を作り直して回すベンチ（OVO-Bench・StreamingBench・OVBench）

**なぜ変えたか**: 公式のコードが読む注釈ファイル 3 つ（`OVOBench_New_32frames.tsv`・`StreamingBench.tsv`・`ovbench_ava_raw_bbox1000.json`）が、公式リポジトリ・HF の MCG-NJU・各ベンチの公式配布のどれにもなかった（11/02〜11/03 に確認）。著者に頼む方法もあるが（外部への投稿なので林の判断、未実施）、林の方針で、まず元のベンチの公開注釈から作り直して回す。

**共通のやり方**: 公式のコードは変えない。作り直した注釈を、公式のコードが読むファイル名で `/mnt/HDD18TB/hayashi/data/_onestreamer_reconstructed/` に置き（動画は元の場所への symlink）、ブランチ `repro/reconstructed` の `paths.json` だけをそこへ向ける。run-id は `recon-*` で、公式の注釈で回す `repro-*` と分ける。作り直しのスクリプトは `repro/reconstruct/build_annotations.py`（入力・出力・変換の規則を冒頭に書いた）。

| ベンチ | 何を作り直したか（元の注釈） | 公式の注釈と同じだと言える根拠 | 違うかもしれない点 | 再現性の下がり方（AI の見立て） |
|---|---|---|---|---|
| OVO-Bench | TSV 全体 3,035 問。元は OVO-Bench 公式の `data/ovo_bench_new.json`（1,640 件）。同梱の `ovobench_timing.json` と中身が完全に一致することを確認。Backward・Real-Time の 1,468 問は 4 択のまま（動画 `chunked_videos/<id>.mp4`、区間 [0, realtime]）。Forward（REC・SSR・CRR）の 172 件は、OVO-Bench 公式の評価コードと同じく `test_info` の各時点を 1 問にした 1,567 問（動画 `chunked_videos/<id>_<k>.mp4`）。質問文は OVO-Bench 公式 `constant.py` の型、REC は数（`integer_match`）、SSR・CRR は Yes/No（`substring_match`） | ・問題の数 1,468 + 1,567 = 3,035 が、HF で配られている切り出し済みの動画の数（3,035 本）とぴったり同じ<br>・OneStreamer の評価コードに、Forward 用としか考えられない `integer_match`・`substring_match` の採点が用意されている<br>・OneStreamer の集計（`metrics.py`）は Backward・Real-Time・Forward の 3 分類の平均で、論文の値もその平均（(81.4+77.9+56.9)/3 = 72.1）になる | ・Forward の質問文（公式の TSV に何が書かれているか分からない。OVO-Bench 公式の型を使った）<br>・ファイル名の「32frames」が何かの選別を意味するか<br>・選択肢の書き方（「A. 」の付け方など）の細かい違い | Backward・Real-Time（2/3 の重み）: **小さい**。元の注釈も動画も公式と同じで、変換は機械的。Forward（1/3 の重み）: **中〜大**。質問文の違いで正答率が変わりうる。論文とは、まず 3 分類ごと（81.4 / 77.9 / 56.9）に比べる |
| StreamingBench Real-Time | TSV 全体 2,500 問。元は StreamingBench 公式 GitHub の `src/data/questions_real.json`（`THUNLP-MT/StreamingBench@8929923`、499 本・2,500 問）。区間は公式の評価コード（`src/benchmark/StreamingBench.py`）と同じ [0, time_stamp]。動画は HF の zip（Real-Time の 10 個）から `real/sample_N/video.mp4` に展開し、`videos/sample_N_real.mp4` のリンクを張った | ・問題の数（2,500）とタスクの内訳が StreamingBench の Real-Time と一致<br>・論文の指標も「Real-Time」で、同じ部分集合 | ・区間の始まり。OneStreamer のコードは「動画と start の組ごとに記憶を共有する」ので、公式の TSV が start = 0 以外を使っていたら、記憶の中身が変わる<br>・選択肢の書き方の細かい違い | **小〜中**。問題の集合は同じ。区間の取り方だけが不確か |
| OVBench | New AVA の JSON だけ（1,396 問・64 本）。元は同梱の `ovbench_split_with_fps_..._bbox1000.json` の中にある `AVA_frame_4fps_new/<id>` の問題で、質問・選択肢・箱（BBox1000）はそのまま、`middle_frame_timestamp` にその問題の end（元動画の絶対秒）を入れた。入力の区間（直前 120 秒・2fps・最大 64 枚・900 秒より前に戻らない）は公式のコードが計算する。New AVA 以外の 5,414 問は公式の注釈のまま | ・64 本の動画 ID が、配られている AVA_RAW の 64 本とぴったり同じ<br>・ファイル名（`ava_raw_frame_processed`）から、同じ問題を元動画から切り出した版と考えられる | ・公式の JSON の問題が同じ 1,396 問か（追加・削除・箱の付け直しがあるか）<br>・同梱の注釈にある古い `AVA/` の 280 問は、公式の New のコードが落とす。公式の JSON にこれに当たる問題があるかは分からない | **中**。論文の値は 16 サブタスクの平均で、そのうち 6 つ（Action Location・Retrieval・Persistence・Trajectory・Sequence・Anticipation）は New AVA だけで作られる。つまり指標の 6/16（37.5%）が作り直した部分に左右される。残りの 10 サブタスクは公式の注釈のまま |

**作り方の手順（列ごとの対応）**: 正本はスクリプト `repro/reconstruct/build_annotations.py`（ブランチ `repro/reconstructed`、冒頭に規則を書いた）。作ったファイルは `/mnt/HDD18TB/hayashi/data/_onestreamer_reconstructed/`（`README.md` 付き）。公式のコード（`run_script/recipes.py` の `records`）が読む列は `index, task, subtask, video, start, end, question, answer, answer_text, A〜E, eval_mode`。

- OVO-Bench（`OVOBench/OVOBench_New_32frames.tsv`）
  - Backward・Real-Time: `task` = 分類名（`backward_tracking`・`real_time_visual_perception`。公式の `metrics.py` の名前）、`subtask` = 元の `task`（EPM など）、`video` = `chunked_videos/<id>.mp4`、`start` = 0、`end` = `realtime`、`question` = 元の `question`、`A〜D` = 元の `options`、`answer` = `gt` の番号を A〜D に、`eval_mode` = `mcq_letter`
  - Forward: 元の 1 件の `test_info` の k 番目を 1 行に。`video` = `chunked_videos/<id>_<k>.mp4`、`end` = その `realtime`。REC: `question` = 公式の REC の型に "How many times did they <activity>?" を入れたもの、`answer` = `count`、`integer_match`。SSR: 公式の SSR の型に `step` を入れたもの、`answer` = `type` が 1 なら Yes・0 なら No、`substring_match`。CRR: 公式の CRR の型に元の `question` を入れたもの、`answer` は SSR と同じ。型と答えの決め方は OVO-Bench 公式の `constant.py`・`utils/OVOBench.py`・`utils/OVOBenchScore.py` に合わせた
  - 11/03 10:35 に REC の質問文を公式の `build_prompt` と同じ "did they" に直して作り直した（`a34bfe7`。最初は "have they" だった。GPU での実行前）
- StreamingBench（`StreamingBench/StreamingBench.tsv`）: 元の 1 本の動画の `questions` の各問を 1 行に。`task` = Real-Time Visual Understanding、`subtask` = `task_type`、`video` = `videos/sample_N_real.mp4`、`start` = 0、`end` = `time_stamp` を秒に（動画より長いときは動画の終わり int(長さ) で止める。公式は ffmpeg の `-t` にそのまま渡すので動画の最後まで切り出され、同じ区間になる。該当は 3 問: 公式注釈の書き間違い `00:12450` の sample_132 と、1 秒だけ長い 2 問。また、配布の動画 sample_332 は 246.4 秒より後が壊れていて読めないので、この動画の 2 問（5:29・8:20）は 246 秒で止める）、`A〜D` = `options` から「A. 」を外したもの、`answer` = 元の文字、`mcq_letter`。元の `time` の欄（"[0:00:00 - 0:00:10]" など）は、公式の評価コードも使っていないので使わない
- OVBench（`OVBench_new/ovbench_ava_raw_bbox1000.json`）: 同梱の注釈の `AVA_frame_4fps_new/<id>` の各問を、`video_id` = `AVA_RAW/<id>` の `questions` に入れた。`question`・`answer`・`answer_type`・`sub_answer_type`・`options` はそのまま、`middle_frame_timestamp` = 元の `end`。形は公式の `ovbench_new.py` の `_flatten_ava_records` が読む形に合わせた

**報告の仕方**: この 3 つの値は「作り直した注釈での参考値」として、`repro-*` の値（ODV-Bench・OVO-Timing）とは分けて書く。著者から本物のファイルが届いたら、同じ手順で `repro-*` として回し直し、違いを比べる。

### 8.2 judge が要るので、採点を回さないベンチ（ProactiveVideoQA・OmniMMI の AP/SI/MD/SG・ViSpeak）

**回さないもの**: 推論（GPU）は回す。回さないのは、推論の結果を判定 LLM（Qwen3-235B-A22B）に採点させる部分だけ。ViSpeak は推論が済み、時刻の判定（公式の関数、judge なし）だけ数えた（6 タスク平均 74.9%）。OmniMMI の PA は judge が要らないので、推論のあとローカルで採点する。

**なぜ回さないか**:
1. 林の方針（2026-11-03）: 費用がかかる方より、注釈を作り直して回せるものを優先する
2. 公式の設定は Alibaba Cloud の DashScope の API（`configs/judge.json`: モデル `qwen3-235b-a22b`、接続先 `dashscope.aliyuncs.com`＝中国本土の北京リージョン、温度 0、思考なし）。使うには Alibaba Cloud のアカウントと API キーが要り、ベンチの質問・参照の答え・モデルの応答を外部のサービスへ送ることになる。アカウントを作るか、どのリージョンを使うかは林の判断
3. 139 で同じ判定 LLM を動かすのは難しい。Qwen3-235B-A22B は BF16 で約 470GB、FP8 でも約 235GB で、139 の GPU（48GB × 4 = 192GB）に載らない。量子化したり小さいモデルにしたりすると、判定の条件が論文と変わる（AI の見積もり。重みの大きさは 235B パラメータからの計算）
4. API の判定は、提供されるモデルの版が変わると点が変わりうるので、推論より再現性が弱い（公式のコードは、成功した判定をキャッシュするので、一度採点すれば同じ点を出し直せる）

**具体的な費用（見積もり）**: 公式の採点コード（`run_script/score.py`）が作る問い合わせを、API を呼ばずにそのまま作って数えた（スクリプト: `repro/estimate_judge_cost.py`、ブランチ `repro/reconstructed` の `3465124`。トークン数は Qwen3 系のトークナイザで数えた）。出力は上限（ProactiveVideoQA 32・OmniMMI 128・ViSpeak 256 token/件）まで出ると仮定した上限値。単価はシンガポール（国際）リージョンの非思考モードで、入力 5.137 元・出力 20.55 元 / 100 万 token（約 $0.70・$2.80。Alibaba Cloud ヘルプセンターの qwen3-235b-a22b のページの値を検索結果から引用。公式ページを直接開いての確認はできなかった）。公式の設定の北京リージョンの単価は確認できていない

| ベンチ | 問い合わせ数 | 入力 token | 出力 token（上限） | 費用（上限） | 数え方 |
|---|---|---|---|---|---|
| ViSpeak | 593 | 0.16M | 0.15M | 約 $0.54 | 推論済みの全 800 問から。時刻が合った問題だけが judge に送られる |
| ProactiveVideoQA | 約 9,000 | 約 1.85M | 約 0.29M | 約 $2.1 | 推論済みの EGO 74 問（6.3 件/問・205 token/件）から全 1,427 問に引き延ばした。TV・WEB は動画が短く応答も少ないはずなので、多めの見積もり |
| OmniMMI（AP・SI・MD・SG） | 3,780（ASR あり・なし 各 1,890） | 0.61M | 0.48M | 約 $1.8（論文の値に要る ASR ありだけなら約 $0.9） | 推論前なので、モデルの応答の代わりに参照の答えを入れて長さを近似した |
| **合計** | **約 13,400** | **約 2.6M** | **約 0.9M** | **約 $4.4（1 ドル 150〜160 円として約 700 円）** | |

→ API の料金そのものは数百円程度で小さい。採点を回すかどうかで効くのは、費用よりも、アカウント・API キーの用意と、外部のサービスへデータを送ってよいかの判断。新しいアカウントには無料枠がある（シンガポールで、有効化から 90 日。量は未確認）。
- 11/03 10:40 林の指示（ProactiveVideoQA も judge が要るので、作り直した注釈の実験を先に）で、ProactiveVideoQA の full を EGO 76/326 で止めた（残っていたワーカー 4 つも止めた）。tmux `os-queue3` を作り直し、OVO-Bench → StreamingBench → OVBench（`recon-*`）→ ProactiveVideoQA（resume）→ OmniMMI の順にした（`54bc9c8`）。10:42 OVO-Bench の smoke を開始
- 11/03 11:00 林の判断: OVBench は記憶の仕組みを使わず（公式の `worker.py` で VLMEvalKit の普通の動画 QA の実行部に回る。区間の画像をまとめて入れて 1 回答える）、オフラインの動画 QA を解いているのに近いので後回しでよい。今のキューの順番（OVO-Bench → StreamingBench → OVBench → ProactiveVideoQA → OmniMMI）のままで、記憶を使う 2 ベンチが先になる。見込み（粗い）: OVO-Bench 約 2.6 日（動画の合計 178 時間 × 約 1.4 倍 ÷ GPU 4 枚 + recent16 約 4 時間）、StreamingBench 約 1 日、OVBench 約 6〜10 時間
- 11/03 11:05 林の指示で順番を組み替えた: StreamingBench を先に（記憶を使うベンチのうち早く終わる、約 1 日）。OVO-Bench は Backward → Real-Time → Forward の順に分けて回す。公式の `--sample-ids` で問題を絞り（`repro/run.sh` に `SAMPLE_IDS_FILE` を追加）、run-id は `recon-bwd`・`recon-rt`・`recon-fwd`（問題の一覧は `repro/reconstruct/ovobench_{backward,realtime,forward}_ids.txt`、631・837・1,567 問）。3 つの結果は、あとで公式の集計関数（`onestreamer.metrics.aggregate`）にまとめて渡して全体の値を出す。そのあと OVBench → ProactiveVideoQA（resume）→ OmniMMI（`0d62111`）。10:49 から回していた OVO-Bench の全問（`recon-full`）は 9 問済んだところで止めた（使わない）。dry-run: Backward 631/3035（2 設定）、StreamingBench 2,500/2,500
- 11/03 14:28 StreamingBench の 1 回目（`recon-full`、11:06〜）が止まった（281/2,500 問済み）。原因は公式注釈（`questions_real.json`）の書き間違い: sample_132 の 1 問の `time_stamp` が `00:12450`（同じ区間のほかの問題は `00:12:20`）で、秒に直すと 12,450 秒になり、動画（約 970 秒）が先に終わって OneStreamer の推論が `Video ended before question boundary` で止まった。公式の評価コードは、この値をそのまま ffmpeg の `-t` に渡すので、動画の最後まで切り出す。それと同じになるよう、注釈を作るスクリプトで、区間の終わりを動画の長さ（整数秒）で止めるようにした（変わったのは 3 問: この 1 問と、動画より 1 秒だけ長い 2 問）。注釈が変わると公式のコードは同じ run-id で続きから回せないので、run-id を `recon2` にして 14:34 から全問をやり直し中（tmux `os-queue4`、`65be6ee`）。1 回目の 281 問は使わない
- 11/03 14:40 OVO-Bench も先に確かめた: 区間の終わり（`realtime`）が切り出し済みの動画より長い問題が 232 問（ほとんどは数十ミリ秒、最大は OCR 1416 の 36 秒）あり、うち 3 問（ASI 603・623、OCR 1416）は同じ理由で推論が止まる。公式は切り出し済みの動画を丸ごとモデルに渡すので、区間の終わりを動画の長さで止めた（ほかの列は変わっていないことを確認。`65be6ee`）。OVO-Bench はまだ回していないので、やり直しの損はない
- 11/03 14:40 見込みの修正: StreamingBench は 1 回目の速さ（3 時間 22 分で 281 問）から、全問で約 30 時間かかる。11/04 の夜（20 時ごろ）に終わる見込み（最初の見込みの約 1 日より遅い）
- 11/04 03:43 StreamingBench の 2 回目（`recon2`）が止まった（1,095/2,500 問済み）。原因は配布の動画 `sample_332` が 246.4 秒より後で壊れていて読めないこと（HF の zip の中身そのもの。zip の CRC は正常で、展開したファイルと同じ中身）。ffmpeg で 499 本を全部読んで確かめ、壊れているのはこの 1 本だけだった。この動画の 5 問のうち、246 秒より後を問う 2 問（5:29・8:20）は、区間の終わりを 246 秒で止めた（ほかの動画と同じく「読める動画の終わりで止める」扱い。動画ファイルは変えていない）。公式の StreamingBench の評価コードでも、ffmpeg の切り出しは読める部分までしか動画を作れないはず（未確認）。論文の著者が同じ壊れた動画を使ったかは分からない
- 11/04 04:57 注釈が変わったので run-id を `recon3` にした。全部をやり直すと約 30 時間かかるので、`recon2` で**動画ごとに全問が済んだ 218 本（1,092 問）はそのまま使い**、残りの 281 本（1,408 問）だけを `recon3` で回している（問題の一覧は `repro/reconstruct/streamingbench_recon3_ids.txt`、`6b593ac`）。recon2 の済んだ問題の注釈の行は recon3 と同じ（変わったのは sample_332 の 2 行で、この動画は recon3 で回す）。採点は、2 つの予測を合わせて公式の採点関数に渡す。同じ動画の問題は記憶を共有するので、途中まで済んでいた動画は丸ごと recon3 でやり直す。tmux `os-queue5`
- 11/04 04:56 2 回目の止まったあと、キューが次の OVO-Bench Backward（`recon-bwd-full`、03:57〜、18 問済）に進んでいたが、StreamingBench を先にする林の指示どおりにするため止めた。OVO-Bench の注釈は変わっていないので、StreamingBench のあと続きから回す（`--resume`）
- 11/04 05:00 見込み: StreamingBench の残り 1,408 問は、recon2 の速さ（13 時間 9 分で 1,095 問、約 83 問/時）から約 17 時間で、11/04 の 22 時ごろに終わる見込み
- 11/04 19:55 林の依頼で GPU 2・3 を空けた（効率が落ちるのは林も承知）。以降は GPU 0・1 の 2 枚で回す。StreamingBench の `recon3` は 1,263/1,408 問済みのところで止めた。公式のコードは GPU の数で問題の割り振りが変わり、同じ run-id では続きから回せないので、動画ごとに全問済んだ 1,263 問は使い、残りの 29 本・145 問を `recon4` で 19:56 から回している（`repro/reconstruct/streamingbench_recon4_ids.txt`、``）。StreamingBench の採点は `recon2`（1,092）+ `recon3`（1,263）+ `recon4`（145）= 2,500 問を合わせる。終わるのは 11/04 の 23 時半ごろの見込み（2 枚で約 42 問/時）。OVO-Bench Backward は `recon-bwd2` で最初から回す（4 枚で 18 問済んでいた `recon-bwd` は使わない）。ProactiveVideoQA の続き（本体の run-id `full`、4 枚で EGO 76/326 まで）も同じ理由で続きから回せないので、キューから外した（回すときに改めて決める）。見込み: 2 枚になったので、OVO-Bench などの残りの時間は 4 枚のときの約 2 倍
