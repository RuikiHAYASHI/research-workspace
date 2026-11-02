---
date: 2026-11-02
project: agentic-streaming-videoqa
topic: OneStreamer-4B の論文の数値を、公式コードと同じ設定で再現する計画
status: draft
tags: [onestreamer, reproduction, dataset, plan]
---

# OneStreamer の再現計画（2026-11-02）

- 作成: 2026-11-02（AI が林と整理）。143 で調べて書いた。続きは 139 の Claude CLI で行う
- 背景: [Streaming モデルの精度比較](../papers/2026-11-02-streaming-model-benchmark-comparison.md)で、OneStreamer-4B（OVO-Bench 72.1 / StreamingBench Real-Time 86.9）が最強クラスだった。林が OneStreamer を動かすと決めた

## 1. 目標と林の判断（2026-11-02）

- 目標: OneStreamer-4B の論文 Table 1 の結果を、公式コードと同じ設定で再現する
- 許容: 「揃えることが不可能ではない環境」が揃っていればよい（GPU が H200 でないなど、揃えようがない差は許す）
- 実験は 139 で行う。GPU は2枚（番号は始める前に林に確認する）。データは 139 にダウンロードし、いずれ NAS にコピーする（NAS への書き込みは林の権限ではできない）
- 保留（あとでやる）:
  - `OVOBench_New_32frames.tsv` と `StreamingBench.tsv` の入手（後述）
  - judge が必要な ProactiveVideoQA・OmniMMI（QA）・ViSpeak の採点（Qwen3-235B を DashScope の API で使う）
- リポジトリ: 公式（`MCG-NJU/OneStreamer`、最新は `338e5fe`）を林の非公開リポジトリとして複製し、公式を `upstream` に登録して、再現用のブランチで作業する
  - 公開リポジトリのフォークは非公開にできないため、空の非公開リポジトリを林が GitHub で作り、AI が push する（143・139 とも GitHub に SSH で接続できる。`gh` は 143 にない）
  - コードは Apache-2.0。`LICENSE`・`NOTICE` は消さない。データと重みはリポジトリに入れない
  - 2026-11-02 時点で、林のリポジトリはまだ作られていない

## 2. 公式の評価コードと設定（公式ドキュメントより）

- 入口: `Eval/run_script/run_eval_8gpu.sh --model OneStreamer-4B --mode infer --run-id <id>`。`--dry-run`、`--limit`、`--gpus`、`--resume` がある
- 設定は `Eval/run_script/recipes.py` と `Eval/Proactive_Eval/OneStreamer/configs/{ovobench,streamingbench}.json` に固定されている。**再現では、コードは変えず、`Eval/run_script/configs/paths.json` と `models.json` だけを書き換える**
- 規模: 1モデルあたり25ジョブ、26,325 設定
- 詳しい設定: 公式リポジトリの `Eval/docs/evaluation_settings.md`（OVO の記憶は 4fps・128 フレームの文脈・1秒ごと、回答は直近16枚 1fps・元の解像度のまま・記憶 12,000 token など）
- 環境（`Eval/docs/environment.md`）: Python 3.10.9、PyTorch 2.6.0+cu124、Transformers 4.57.6、flash-attn 2.7.4.post1、OpenCV 4.13.0.92 を `--no-deps`、NumPy 1.26.4
  - OpenCV のバージョンが違うと StreamingBench のデコードした画素が変わる、と公式に書かれている。バージョンは必ず合わせる
- モデル:
  - `MCG-NJU/OneStreamer-4B`（HF。2026-11-02 の sha は `fba29e6`）
  - `Qwen3-VL-4B-Instruct_no_special_token`（基盤モデルの行の比較用。`Qwen/Qwen3-VL-4B-Instruct` に special token を足さないもの、と読めるが要確認）

## 3. データセット

公式の置き方は公式リポジトリの `Eval/docs/data_layout.md`。動画のファイル名とフォルダ構造は、注釈が参照するとおりにする。

| ベンチマーク | 入手先（HF） | 大きさ（zip・tar） | 置き方・注意 |
|---|---|---|---|
| OVO-Bench | `JoeLeelyf/OVO-Bench` | chunked_videos 144GB ＋ src_videos 44GB | QA は TSV の `video` 列を参照。**OVO-Timing（`ovobench_timing.json`）は `Ego4D/clips/...` のような元動画のパスを使うので src_videos も必要**。143 の `/mnt/HDD10TB-2/hayashi/data/OVO-Bench` に chunked の tar がある（展開済みは300本だけ） |
| StreamingBench | `mjuicem/StreamingBench` | 203GB（zip 37個） | 評価は Real-Time 部分（sample_id が `streamingbench-realtime-*`）。`StreamingBench.tsv` が別に必要 |
| OVBench | `MCG-NJU/OVBench` | 約 200GB（ArgoVerse・BDD・COIN・Charades・HACS・HiREST・LaSOT・YFCC100M・AVA_RAW） | 注釈は公式リポジトリに同梱。New AVA には `OVBench_new/ovbench_ava_raw_bbox1000.json` と `AVA_RAW/` が要る（この JSON の入手先は未確認） |
| ODV-Bench | `MCG-NJU/ODV-Bench` | 14GB（zip 3つ） | `TOI_Recognition/`・`TR_Analysis/`・`TS_Retrieval/`。注釈は同梱 |
| ProactiveVideoQA | `wangyueqian/ProactiveVideoQA` | 43GB | `EGO/TV/VAD/WEB` の下に `anno.json` と `videos/`（採点は保留） |
| OmniMMI | `bigai-nlco/OmniMMI` | 62GB | 5タスクの JSON と `videos/`。HF の動画は `clips/` にあるので、置き方を要確認（採点は一部保留。PA はローカルで採点できる） |
| ViSpeak-Bench | `fushh7/ViSpeak-Bench` | 4GB | ルートの直下にタスクのフォルダを置く（1段多く挟まない。採点は保留） |

- 合計は圧縮で約 720GB。139 の `/mnt/HDD18TB` は 2026-11-02 時点で空き 4.2TB。展開後に zip・tar を消すかは林に確認する
- 置き場所の案: `/mnt/HDD18TB/hayashi/datasets/onestreamer-eval/<公式の名前>/`（`paths.json` の各キーに合わせる）

### データを実験の設定に揃えるための決まり

1. 動画は再エンコード・縮小・切り出しをしない（10/29 の試行では、A4000 のメモリ不足で直近16枚を縮めた。139 の A6000 48GB では縮めない）
2. 注釈は公式に同梱された版（BBox1000 版、`ovobench_timing.json` など）だけを使う
3. `--dry-run` で件数（25ジョブ・26,325設定）を確かめ、各ジョブ1問（`--limit 1`）の試走で、すべての動画が開けることを確かめてから全体を回す
4. 公式との違いは、すべて experiments/ のログに書く

### 入手先が分からないもの（保留）

- `OVOBench_New_32frames.tsv`（列: `index, task, subtask, video, start, end, question, answer, answer_text, A〜E, eval_mode`）
- `StreamingBench.tsv`（同じ列）
- `OVBench_new/ovbench_ava_raw_bbox1000.json`
- 公式リポジトリ・HF の MCG-NJU・OVO-Bench 公式のどれにもなかった。案は (a) 著者に GitHub の Issue で頼む（外部への投稿なので林が判断）、(b) 公式の注釈から作り直す（問題の選び方が論文と同じだと保証できない）

## 4. 進める順番

1. 139 で、林の割り当ての GPU 番号と、データの置き場所・zip を消すかを確認する
2. 139 でデータをダウンロードする（tmux）。保留のない順に: ODV-Bench（小さく完結）→ OVO-Bench（src と chunked）→ OVBench → StreamingBench → ProactiveVideoQA・OmniMMI・ViSpeak
3. 公式の環境（conda `onestreamer-eval`）を 139 に作る。重みを置く
4. 林のリポジトリができたら、公式 `338e5fe` を push して、再現用のブランチを作る。`paths.json`・`models.json` だけ書き換える
5. ODV-Bench と OVBench（TSV が要らない）で `--dry-run` → `--limit 1` → 全体
6. TSV が手に入ったら OVO-Bench と StreamingBench（論文の看板の数値）
7. 結果を論文の値と比べ、experiments/ に記録する

## 5. 関連

- これまでの試行: [LongVideoBench での公開コードの試行](../experiments/2026-10-27-public-text-memory-baselines-lvb.md)、[OVO-Bench での試行](../experiments/2026-10-29-ovo-bench-public-baselines-v6g.md)
- 前回の作業用の clone: 143 の `/mnt/HDD10TB-2/hayashi/2026_10_hayashi_public_text_memory_baselines/OneStreamer`（`lvb/`・`ovo/` の追加と `engine.py` の修正が入っているので、再現の土台にはしない）
