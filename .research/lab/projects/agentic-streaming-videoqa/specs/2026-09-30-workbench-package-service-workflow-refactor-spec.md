---
date: 2026-09-30
project: agentic-streaming-videoqa
type: implementation
status: draft
sequence: 1
sequence_total: 4
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 2b5f8309ed380951d812c3f2191f57ce30fb7ccd
depends_on: []
source_brainstorm:
  - 2026-09-30-workbench-refactor-architecture.md
---

# Workbench Package / Service / Workflow 構造refactor spec

## 1. 目的

現在のWorkbenchは機能的には動作しているが、`agent/`、`model/`、`interfaces/`、`dataset/`、`records/`へ責務が混在し、研究の一本道「Dataset → Video Stream → Situation → Memory → Answer → Record」がコード構造から読み取りにくい。

このspecでは**外部挙動を変えず、研究処理の依存方向を一方向のDAGに整理する**。初見の研究者が大きなファイルだけを読めば、細かいhelperを追わずに処理全体を説明できる状態を成功条件とする。

## 2. 採用する構造

```text
src/longvideoqa_workbench/
├── agents/
│   ├── __init__.py
│   ├── agent.py
│   ├── service.py             # AgentService
│   ├── qwen3_vl.py
│   └── fake.py
├── workflow/
│   ├── __init__.py
│   ├── video_qa.py            # VideoQAWorkflow（全体監督）
│   ├── team.py
│   ├── situation.py           # SituationTask
│   ├── memory.py              # MemoryTask
│   └── answer.py              # AnswerTask
├── datasets/
│   ├── __init__.py
│   ├── service.py             # DatasetService
│   ├── longvideobench.py
│   └── fake.py
├── streaming/
│   ├── __init__.py
│   ├── service.py             # VideoStreamService
│   ├── reader.py
│   └── sampling.py
├── browser/
│   ├── __init__.py
│   ├── service.py             # BrowserService
│   ├── catalog.py
│   ├── index.py
│   ├── search.py
│   ├── library.py
│   ├── media.py
│   └── translation.py
├── runtime/
│   ├── __init__.py
│   ├── service.py             # RunService
│   └── session.py
├── records/
│   ├── __init__.py
│   ├── service.py             # RecordService
│   └── run.py
├── presentation/
│   ├── __init__.py
│   ├── service.py             # PresentationService
│   ├── web_view.py
│   └── text_trace.py
├── entrypoints/
│   ├── __init__.py
│   ├── cli.py
│   └── server.py
├── config/
├── core/
└── web/
```

`views/`ではなく`presentation/`を採用する。ここは推論を行うViewではなく、保存済みrecordを人間向けに投影するread-only層であるため。

## 3. 命名と責務

### 3.1 Workflow / Task / Service

- **VideoQAWorkflow**: 研究フロー全体の短い監督。Dataset/Stream/Task/Recordの呼出し順だけを管理する。
- **SituationTask / MemoryTask / AnswerTask**: Agentに与える入力を構築し、1回推論を呼び、役割固有outputを検証する。
- **AgentService**: Agent定義とmodel backendを外部へ提供する窓口。
- **DatasetService**: QuestionSample等を取得するdataset接続の窓口。
- **VideoStreamService**: 動画を先頭から読み、window/samplingを提供する窓口。
- **RecordService**: machine artifactの保存・読取窓口。
- **PresentationService**: recordからWeb表示/text traceを決定的に生成するread-only窓口。
- **BrowserService**: dataset検索・お気に入り等の独立Browser機能の窓口。
- **RunService**: HTTP/CLIからのstart/next/restart/cancelとsession lifecycleを管理。
- **entrypoints**: HTTP routingとCLI引数処理だけを担当。

### 3.2 Package boundary

他packageは内部module/private helperを直接importせず、原則として各packageの`__init__.py`から公開されるServiceまたは公開DTOだけを利用する。共有DTOは`core/`へ置く。

横方向のService→Service連鎖を増やさず、研究フローの組合せは原則`VideoQAWorkflow`で見える形にする。

## 4. VideoQAWorkflowの読みやすさ

`workflow/video_qa.py`は「研究の流れ」が一目で分かることを最優先し、HTTP、thread、cancel implementation、JSON serialization、Qwen固有処理を持たない。

概念上は次の粒度を維持する。

```python
for window in windows:
    situation = situation_task.run(...)
    memory = memory_task.run(...)
    records.record_turn(...)

answer = answer_task.run(...)
records.record_answer(...)
```

目安として50--100行程度を狙うが、行数そのものをacceptance criterionにはしない。

## 5. Agentとmodelの統合

現`model/qwen3vl.py`と`model/fake.py`は`agents/`へ移す。`agents/qwen3_vl.py`はQwenのload/capability/image-video入力/generateだけを知り、Situation/Memory/Answerの意味を知らない。

Agentは「model + prompt ID + generation + role metadataを持つ1回の生成単位」とし、役割固有JSON validationはTask側へ置く。

この段階では**同一Qwen backendを3 roleで共有する現在挙動を維持**し、Agent別model選択はStage 2以降のconfig contractで扱う。

## 6. Dataset / Browserの分離

`datasets/`にはLongVideoBench/Fakeのdataset固有接続だけを残す。`catalog/index/search/library/media/translation`は`browser/`へ移す。

Browserは研究推論Workflowから独立した枝とし、Browser閲覧によって推論run/turnを開始しない。

## 7. Records / Presentation

`records/`はmachine SSOTのJSON/JSONLと最新snapshotの保存・読取だけを担当する。

`presentation/`は保存済みrecordだけを入力にし、推論状態を変更せず次を生成する。

- 現行Webに必要な人間向けprojection。
- テキストtrace。`run_trace.md`をrun artifactの派生物として保存可能にする。
- 旧runでは保存ファイルが無くてもrecordから同内容を再生成できる。

基本text traceは各windowで実行されたAgentの主要出力を順に残す。

```text
[00:00 - 00:04] Situation Agent
<主要なSituation text>

[00:00 - 00:04] Memory Agent
<主要なMemory text>

...
[END] Answer Agent
<final answer>
```

prompt/raw JSON/event/frame/timestamp/latency等の詳細はmachine recordおよび詳細表示に残す。

Presentation生成失敗を推論runの失敗として扱わず、Recordが残っていれば再生成可能にする。

## 8. 変更しない契約

- Qwen `video_clip`、sample_fps、`do_sample_frames=False`。
- Situation/Memory/Answerのprompt本文とJSON schema。
- `none/previous_text`。
- EOF-only Answerと`insufficient_evidence`。
- existing run artifactの既存ファイル形式。
- HTTP endpointとresponseの既存意味。
- old image_list runの閲覧/復元。
- foreground server / port 8765 / Ctrl+C運用。
- 実Qwen/GPU挙動。

## 9. 対象外

- Config schemaの再設計（Stage 2）。
- Prompt CRUD/履歴/UI（Stage 3）。
- Dataset別user data/cache migration（Stage 4）。
- early answer / Memoryのcontinue-answer判定。
- 実Qwen/GPU/LongVideoBench full run。
- model download。
- scientific behavior変更。

## 10. 実装順

1. preflight: remote main/local HEAD/worktree/dirty/import元を確認。
2. 公開Service/DTOと依存ルールをtestで固定。
3. `agents/`と`workflow/`へ移動し、CLIとserverの重複orchestrationを`VideoQAWorkflow`へ集約。
4. dataset/browser、runtime/entrypointsを分離。
5. RecordService/PresentationServiceを分離し、既存Web projectionとtext traceを同じprojection sourceへ接続。
6. import cleanup、旧moduleの一時re-exportは既存public importを壊す場合だけ最小限にする。
7. 全短時間回帰を実行。

## 11. Success Criteria

- 現行181件相当のunit/Fake/browser testが非回帰。
- CLI/API endpoint、既存artifact、prompt/output schemaが変わらない。
- CLIとWebが同じ`VideoQAWorkflow`を利用し、独立した推論進行実装を持たない。
- package外からprivate implementationを直接importする新規依存がない。
- `workflow/video_qa.py`だけでSituation→Memory→EOF Answerの流れを説明できる。
- Web human viewとtext traceが同じrecord projectionから作られる。
- GPU/実Qwenを使わず検証可能。

## 12. Ambiguity Gate

blocking: なし。現在のユーザー指示でpackage名・一方向依存・Presentation分離・短い全体監督の方向は十分に固定されている。

non-blocking:
- 個々のhelper名、dataclass名、ファイル内private関数は既存styleへ合わせる。
- import cycle回避のため公開DTOを`core/`へ残すか各packageへ置くかは、依存方向を壊さない最小配置を選ぶ。
- legacy import re-exportは実際に既存test/public APIが必要とする場合のみ。

## 13. Gate

本書は`draft`。ユーザーが本spec内容を承認するまでコード変更不可。承認後はStage 1だけをengineering-taskへ渡し、Stage 2以降を同時実装しない。
