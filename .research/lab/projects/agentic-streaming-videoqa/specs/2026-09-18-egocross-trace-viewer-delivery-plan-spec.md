---
date: 2026-09-18
project: agentic-streaming-videoqa
status: draft
topic: egocross-trace-viewer-delivery-plan
supersedes: 2026-09-18-egocross-trace-viewer-implementation-spec.md (implementation sequencing)
source: viewer implementation spec + 2026-09-18 user-directed branch and commit policy
last_updated: 2026-09-18
---

# EgoCross Trace Viewer 実装計画（Step / micro-step版）

## 位置付け

本書は`2026-09-18-egocross-trace-viewer-implementation-spec.md`の要件、表示設計、API契約、成功条件を維持し、実装順だけをStep branchとmicro-step commitへ再構成する改訂planである。以後の実装順・branch・commitは本書を正本とする。

目的は、既存EgoCross Agent traceをloopbackのread-only viewerで表示し、初見者が「現在画像 → 観測文 → action → text state」をframe単位で読めるようにすることである。Qwen実行、最終QA、accuracy、live監視、外部公開は対象外とする。

## 開始状態

- 実装repository: `/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation`
- 既存の未commit文書2件は`d7a1dc5`（`docs: explain agent run and structure`）として確定済み。実行コード、dataset、artifactは変更していない。
- 今回の開始branchは`feat/step-08-trace-viewer-contract`であり、`d7a1dc5`から作成済みである。
- 現在branchの前身、`main`、既存traceは変更しない。GitHubへのpush、PR、mergeは本planの対象外である。

```text
feat/step-07-agent-reproducibility
└── feat/step-08-trace-viewer-contract        （作成済み、基準 d7a1dc5）
    └── feat/step-09-trace-viewer-server
        └── feat/step-10-trace-viewer-ui
            └── feat/step-11-trace-viewer-verification
```

## 共通のbranch・commit規約

- **1 Step = 1 branch**。Step末尾の必須testが成功してから、直前StepのHEADから次branchを作る。
- **1 micro step = 1 commit**。複数micro stepを同じcommitに混在させない。
- commit titleは下表の文言を使う。本文には`対象`、`変更`、`理由`、`検証`、`影響`、`次`を日本語で各1行ずつ記載する。
- micro stepごとに対象diffと対応testを確認する。Step末尾testが失敗した場合は、同じbranchで`fix:`または`test:` commitを追加し、test成功まで次branchを作らない。
- `outputs/`、dataset画像、model weight、credentialをcommitしない。Qwen実行、dataset更新、既存artifactの書換えをしない。

## Step 08: deterministic event provenance contract

**Branch:** `feat/step-08-trace-viewer-contract`
**目的:** modelがeventのframe番号を生成する現行契約をなくし、Reducerがcurrent `frame_index`からevent provenanceを決定的に付与する。

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 08.1 | `refactor: separate event proposal from state provenance` | policy event proposalを、frame provenanceを持つactive `OpenEvent`から分離する。policy JSONから`first_frame` / `last_evidence_frame`を除き、旧fieldを拒否する。 |
| 08.2 | `feat: derive event provenance from frame index` | Reducerへcurrent `frame_index`を渡す。ADDは両frameをcurrent index、UPDATEは開始frameを維持し最終根拠frameをcurrent indexにする。CLOSE_EVENTの閉鎖frameもtraceへ残す。 |
| 08.3 | `feat: version deterministic event provenance` | policy/state schema versionとrun metadataを更新し、新runをlegacy traceと区別する。旧JSONLのmigration・書換えはしない。 |
| 08.4 | `test: cover deterministic event provenance` | ADD / UPDATE / CLOSE_EVENTのframe provenance、legacy policy JSON拒否、state連続性、current-image-only境界をtestする。 |
| 08.5 | `docs: describe deterministic event provenance` | event frameの意味とlegacy trace表示互換を利用文書へ記載する。 |

**変更対象:** `agent.py`、`agent_policy.py`、`reducer.py`、`agent_pipeline.py`、`run_metadata.py`、対応test・文書。
**Step末尾test:** `.venv/bin/python -m pytest -q`、`python3 -m compileall egocross_observation scripts`。
**次branch:** test成功後に`git switch -c feat/step-09-trace-viewer-server`。

## Step 09: read-only trace viewer server

**Branch:** `feat/step-09-trace-viewer-server`
**目的:** Qwenをloadせず、trace、metadata、manifest、参照画像をloopbackのread-only HTTP APIで安全に供給する。

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 09.1 | `feat: add read-only trace run loader` | `viewer.py`へrun一覧、metadata、JSONLを読むloaderを追加し、decode-only / observe / agentと壊れたrunを表示用に正規化する。 |
| 09.2 | `feat: verify manifest context for viewer runs` | metadataのmanifest SHA-256とrecord IDを照合し、一致する質問・選択肢だけを返す。不一致・欠損は利用不能状態にする。 |
| 09.3 | `feat: serve loopback trace viewer endpoints` | `scripts/serve_trace_viewer.py`と標準ライブラリhandlerを追加し、`/api/runs`、run detail、trace参照済み画像だけを`127.0.0.1`で提供する。 |
| 09.4 | `test: cover trace viewer data boundaries` | JSONL順、hash不一致、欠損artifact、path traversal、未参照画像、存在しないrun/indexを合成fixtureでtestする。 |

**Step末尾test:** `.venv/bin/python -m pytest -q`、`python3 scripts/serve_trace_viewer.py --help`、synthetic fixtureのloopback API smoke。
**次branch:** test成功後に`git switch -c feat/step-10-trace-viewer-ui`。

## Step 10: single-page viewer UI

**Branch:** `feat/step-10-trace-viewer-ui`
**目的:** 初見者向け説明と、画像・観測・action・state diffをframe単位で読む画面を、外部frontend dependencyなしで実装する。

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 10.1 | `feat: add trace viewer static shell` | `viewer_static/`のHTML、CSS、JavaScript最小shellとpackage-data設定を追加する。 |
| 10.2 | `feat: explain agent trace and navigate frames` | 常時説明、action glossary、run概要、manifest検証状態、frame番号・相対時刻・action名のnavigatorを実装する。色だけで意味を表さない。 |
| 10.3 | `feat: render frame observation and state diff` | 選択frameの画像、observation、action・confidence・reason、決定的state diff、state afterの4区画を表示する。LLM要約・翻訳を追加しない。 |
| 10.4 | `feat: render viewer details and errors` | model/schema/timing/logical path/raw policy responseを詳細へ置き、error、manifest不一致、画像欠損、legacy provenanceを明示する。 |
| 10.5 | `test: package viewer static assets` | static asset配信、HTML特殊文字のtext表示、mode別の欠損表示をtestする。 |

**Step末尾test:** `.venv/bin/python -m pytest -q`、`python3 -m compileall egocross_observation scripts`、既存5-frame traceのread-only local smoke。
**次branch:** test成功後に`git switch -c feat/step-11-trace-viewer-verification`。

## Step 11: viewer verification and usage guide

**Branch:** `feat/step-11-trace-viewer-verification`
**目的:** APIとUIを結合して検証し、Edge等で開く手順と表示範囲を固定する。GPU inferenceは行わない。

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 11.1 | `test: cover viewer end-to-end trace flow` | synthetic agent traceで、run選択、frame切替、画像取得、observation、action、state diff、error状態をHTTP経由で検証する。 |
| 11.2 | `docs: document local trace viewer usage` | READMEと利用文書へ、loopback起動、EdgeでのURL、表示するもの / しないもの、artifact非変更、医療映像の注意を記載する。 |

**Step末尾test:** `.venv/bin/python -m pytest -q`、`python3 -m compileall egocross_observation scripts`、既存5-frame traceを使う`127.0.0.1`上の手動browser受入。
**完了条件:** Edgeで`http://127.0.0.1:<port>/`を開き、画像・観測・action・state diffをframeごとに確認できる。Qwen実行やartifact書換えは起こらない。

## Gateと後続run

- このviewer実装が完了し、Step 08のprovenance修正を含むclean commitが得られるまで、4-domain（39 frame）のAgent runは開始しない。
- viewerの実装完了と、GPU Agent runの実行許可は別である。4-domain runは`2026-09-18-egocross-demo-agent-run-spec.md`に従う。

## Implementation Handoff

- approved spec: 本文書（現時点ではdraft）
- 実装目的: 既存traceを安全に読取り、初見者が因果的な観測・記憶更新を閲覧できるloopback viewerを作る。
- 基準repository/commit: `feat/step-08-trace-viewer-contract`、基準`d7a1dc5`。
- 変更scope: deterministic event provenance、read-only server、static UI、test、利用文書。
- 対象外・維持条件: Qwen実行、final QA、accuracy、live監視、外部公開、既存artifact変更は行わない。
- success criteria: 各Step末尾testとStep 11の手動browser受入を満たす。
- 許可されている短時間検証: 各Stepのunit / API / loopback smoke。GPU inferenceは含まない。
- 長時間runの許可状態: 未許可。4-domain・39 frame Agent runは別specの明示許可待ち。
- 未検証予定: Agent actionの意味的品質、質問への正答、Agentの研究上の有効性。

## 関連記録

- `2026-09-18-egocross-trace-viewer-implementation-spec.md`
- `2026-09-18-egocross-demo-agent-run-spec.md`
- `.research/secretary/notes/brainstorm/2026-09-18-egocross-agent-trace-readability.md`
