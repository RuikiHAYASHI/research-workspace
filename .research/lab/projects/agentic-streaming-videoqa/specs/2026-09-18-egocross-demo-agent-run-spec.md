---
date: 2026-09-18
project: agentic-streaming-videoqa
status: draft
topic: egocross-demo-agent-run
source: 2026-09-18-egocross-demo-video-selection brainstorm
last_updated: 2026-09-18
---

# EgoCross 4-domain Agent表示用run spec

## 目的

ブラウザviewerで、初見者が「現在画像 → 観測文 → Agent action → text state」の時系列を読めるように、EgoCrossの4 domainから約10 frameの画像列を各1 runずつ`--agent`で処理する。

成果物は表示・質的レビュー用の4つのAgent traceであり、final QA、回答選択、accuracy、Agent性能の定量比較ではない。各frameでcurrent imageだけを観測し、previous text stateと観測文だけでstate更新を行う既存の因果境界を維持する。

## 採用内容

standard manifestは`/mnt/HDD18TB/hayashi/data/EgoCross/egocross_testbed/egocross_testbed_imgs.json`、dataset rootは`/mnt/HDD18TB/hayashi/data/EgoCross`を使う。各recordの`video_path`順を変更せず、全frameを処理する。

| 順序 | record ID | domain | frame数 | 質問形式 | 選定理由 |
| ---: | ---: | --- | ---: | --- | --- |
| 1 | 545 | ENIGMA | 10 | dominant held-object identification | 電子機器の机上作業から、手と電動工具が前景になる変化を読む。最初の実runとして、医療映像を含まない分かりやすい例にする。 |
| 2 | 203 | EgoPet | 11 | interaction temporal localization | 猫の視点で別の猫との相互作用を追う。動物の移動・接近に対するstate更新を見る。 |
| 3 | 823 | ExtrameSportFPV | 8 | action sequence identification | FPVスポーツの高速な一人称視点で、前二者と異なる視点・運動変化を含める。 |
| 4 | 14 | CholecTrack20 | 10 | action temporal localization | 腹腔鏡の術野と器具の変化を追う。血液を含む医療映像であることをviewer上でも明示する。 |

合計は39 frameである。ID 823はdataset内の対象候補が8 frameであり、「10 frame程度」の範囲として採用する。

## 前提と実行前Gate

1. viewer spec `2026-09-18-egocross-trace-viewer-implementation-spec.md` のevent provenance修正（eventのframe番号をcurrent `frame_index`から決定的に付与する契約）が実装・test済みであること。このrunはその修正を含むcommitから作る。現時点の`0288519`が出力したlegacy traceは、event frameの意味が表示に使えないため、表示用の新規runには使わない。
2. 実行repository `/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation` は、上記修正を含むcommitをcheckoutし、worktreeがcleanであること。現在確認済みの`0288519`上の未commit `docs/`変更は、ユーザーの変更として変更・commit・削除しない。
3. `.venv`にQwen実行依存があり、GPU割当が利用可能であることを、modelをloadしないpreflightで確認する。GPU物理番号は実行時にのみ環境変数で与え、source、config、run metadataへ固定しない。
4. selected recordの全画像がdataset rootに存在し、manifest hashが実行ごとに`run_metadata.json`へ保存されること。選定時点では4 recordの全39画像の存在を確認済みである。

このGateを満たせない場合はrunを開始しない。viewer実装の承認・実装と、GPU上で39 frameを処理する本runの許可は別である。

## 固定する実行条件

| 項目 | 固定内容 |
| --- | --- |
| 実行モード | `--agent`。`--observe`は併記しない。 |
| 観測入力 | 質問・選択肢・current frame metadata・現在画像1枚だけ。 |
| policy入力 | 質問・選択肢・previous text state・current-frame observationだけ。画像・過去画像・future frame・final answerを渡さない。 |
| model | 既存CLI既定の`Qwen/Qwen3-VL-4B-Instruct`。実際のcheckpoint revisionはmetadataに記録された値を正本とする。 |
| generation | `--max-new-tokens 256`、既存adapterの決定的生成設定（`do_sample: false`）を使う。 |
| dtype / device map | CLI既定の`auto`を使う。実行後にmetadataから実行条件を確認する。 |
| 入力順 | manifestの`video_path`配列順。sort、skip、先読み、過去画像の再入力をしない。 |
| output root | repository内の`outputs/2026-09-18-demo-agent/`。各CLI実行はUUID付き新規run directoryを作る。 |
| overwrite / resume | 上書き・resume・自動retryをしない。失敗時はそのrunを残して停止し、原因を確認してから次の判断を行う。 |

`outputs/`、dataset画像、model weight、credentialをGitへ追加しない。

## 実行手順

実行前にrepository rootへ移動する。`<GPU_ALLOCATION>`はその時点で割り当てられた値へ置換するが、ここでは特定番号を指定しない。

```bash
cd /mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation
CUDA_VISIBLE_DEVICES=<GPU_ALLOCATION> .venv/bin/python scripts/check_qwen_runtime.py
.venv/bin/python -m pytest -q
```

preflightとtestが成功した場合に限り、次を**一件ずつ順に**実行する。各commandの標準出力に出る`saved trace: ...`を記録し、直後の検証を通過してから次recordへ進む。

```bash
CUDA_VISIBLE_DEVICES=<GPU_ALLOCATION> .venv/bin/python scripts/observe_egocross.py \
  --record-id 545 --max-frames 10 --agent --max-new-tokens 256 \
  --output-root outputs/2026-09-18-demo-agent

CUDA_VISIBLE_DEVICES=<GPU_ALLOCATION> .venv/bin/python scripts/observe_egocross.py \
  --record-id 203 --max-frames 11 --agent --max-new-tokens 256 \
  --output-root outputs/2026-09-18-demo-agent

CUDA_VISIBLE_DEVICES=<GPU_ALLOCATION> .venv/bin/python scripts/observe_egocross.py \
  --record-id 823 --max-frames 8 --agent --max-new-tokens 256 \
  --output-root outputs/2026-09-18-demo-agent

CUDA_VISIBLE_DEVICES=<GPU_ALLOCATION> .venv/bin/python scripts/observe_egocross.py \
  --record-id 14 --max-frames 10 --agent --max-new-tokens 256 \
  --output-root outputs/2026-09-18-demo-agent
```

既存CLIは1 commandにつき1 recordを処理し、processごとにmodelをloadする。このspecでは4 recordを1 processへまとめるbatch launcherを追加しない。

## 各run直後の検証

run directoryごとに、次を確認する。

1. `frames.jsonl`と`run_metadata.json`が存在する。
2. JSONL行数が対象frame数（ID 545: 10、203: 11、823: 8、14: 10）と一致する。
3. 全行の`record_id`が指定ID、`frame_index`が`0..N-1`の連番、`error`が`null`である。
4. 全行に非空の`observation`、`agent.parsed_decision`、`agent.state_before`、`agent.state_after`がある。
5. frame 1以降で、前行の`agent.state_after`と次行の`agent.state_before`が一致する。
6. metadataの`mode`が`agent`、record ID / frame countが指定値、manifest SHA-256、model ID / revision、code revision、generation parameters、prompt / state schema versionが記録されている。
7. metadataのcode revisionが、実行前Gateで確認したprovenance修正版commitと一致する。

不一致、画像decode失敗、Qwen観測失敗、policy JSON parse失敗、Reducer失敗、GPU/runtime失敗のいずれかが起きた場合、そのrecordより後のrunを自動継続しない。flush済みのtraceとmetadataを残し、失敗record・frame・`error_phase`・error本文を実験ログへ報告する。

## 成功条件と未検証項目

### 実装・運用上の成功

- 4つの新規run directoryが専用output rootに作られ、合計39行のerror-free Agent traceが得られる。
- 各frameに、画像由来observation、検証済みaction、連続するstate before/after、再現性metadataが保存される。
- 4 domainのviewerで、質問文脈、画像、観測、action、state diffをframe単位で閲覧できる。
- 既存run、dataset、model cache、source code、未commit文書を変更しない。

### このspecで評価しないこと

- 選択肢の正解、final QA、accuracy、質問への回答性能。
- action 5種類すべての出現。既存5-frame smokeは`ADD`と`UPDATE`だけであり、候補選定はaction多様性を保証しない。
- Agentのevent / watch / uncertaintyの意味的な正しさ。定型的なwatchや質問と無関係なeventも、質的レビューで失敗Evidenceとして残す。
- 957 record全体、長期Memory、baseline比較、学習、LoRA、multi-timescale memory、動的chunk。

## 対象外・互換性

- `sequential_loader`、EgoCross manifest、dataset画像、既存`frames.jsonl`、既存`run_metadata.json`を編集しない。
- Qwen prompt、model ID、state構造をこのrunのためだけに変更しない。event provenance修正以外のAgent実装変更は別specとする。
- viewerはartifactをread-onlyで表示する。ブラウザからQwen実行、停止、run削除はしない。
- ID 14の医療映像は、閲覧者へ明示して表示する。別domainに差し替える場合は、このspecを実行せず、新たなrecord選定を行う。

## Blocking / Non-blocking

### Blocking

- event provenance修正とviewerの基礎実装が未完了であり、現時点では表示用の新規Agent runを開始できない。
- 実行時にcleanなprovenance修正版commitと利用可能なGPU割当が必要である。
- 本文書は`draft`であり、39 frameのQwen / GPU実行を許可しない。

### Non-blocking

- 4 commandの間でGPU割当を変更してよい。ただし、各runの実行環境を実験ログへ記録する。
- viewerの表示順はrecord ID順でなく、ここで定めたENIGMA → EgoPet → ExtrameSportFPV → CholecTrack20順とする。
- output run IDはCLIのUTC timestampとUUIDで自動生成し、実行前に固定しない。

## Approval Gate

このspecは、ユーザーが医療映像を含む4 domain構成を採用することを確認して保存した`draft`である。次の二つは別途必要である。

1. viewer / event provenance実装specを承認し、実装・test・commitまで完了すること。
2. この4本・39 frameのGPU Agent runを明示的に実行許可すること。

## Execution Handoff

- approved spec: 本文書（現時点ではdraft）
- 実行目的: 4 domain・39 frameの既存EgoCross画像列から、viewerで読めるAgent traceを作る。
- 基準repository/commit: viewerのevent provenance修正を含むclean commit。`0288519`とそのdirty worktreeは実行基準にしない。
- 実行scope: ID 545 (10)、203 (11)、823 (8)、14 (10) を各1回、`--agent`で全frame処理する。
- 対象外・維持条件: final QA、accuracy、全件run、prompt変更、既存artifact変更は行わない。
- success criteria: 4 run、39行、全行error-free、state連続性、metadata完全性、viewerでの閲覧可能性。
- 許可されている短時間検証: preflightとpytestのみ。Agent実行は別途許可が必要。
- 長時間runの許可状態: 未許可。39 frameのGPU Agent runは明示許可待ち。
- 未検証予定: actionの意味的品質、質問への正答、action多様性、Agentの研究上の有効性。

## 関連記録

- `.research/secretary/notes/brainstorm/2026-09-18-egocross-demo-video-selection.md`
- `specs/2026-09-18-egocross-trace-viewer-implementation-spec.md`
- `experiments/2026-09-16-egocross-agent-text-state-smoke.md`
- `specs/2026-09-16-egocross-observation-agent-addendum-plan.md`
