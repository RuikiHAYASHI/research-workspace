---
date: 2026-09-30
last_updated: 2026-10-01
project: agentic-streaming-videoqa
type: implementation
status: implemented
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
- Stage 1移行前の旧compatibility directoryが、確認済みの外部契約なしに重複して残っていない。
- repository内testが旧compatibility importを理由に旧directoryを存続させていない。
- Stage 1説明文書が現行package構造を指し、存在しない旧architectureを説明していない。
- `workflow/video_qa.py`だけでSituation→Memory→EOF Answerの流れを説明できる。
- Web human viewとtext traceが同じrecord projectionから作られる。
- GPU/実Qwenを使わず検証可能。

## 12. Ambiguity Gate

blocking: なし。現在のユーザー指示でpackage名・一方向依存・Presentation分離・短い全体監督の方向は十分に固定されている。

non-blocking:
- 個々のhelper名、dataclass名、ファイル内private関数は既存styleへ合わせる。
- import cycle回避のため公開DTOを`core/`へ残すか各packageへ置くかは、依存方向を壊さない最小配置を選ぶ。
- legacy import re-exportは実際に既存test/public APIが必要とする場合のみ。

## 13. Git Branch / Commit Strategy

Stage 1は、**Stage用のintegration branchを1本作り、その配下の各実装stepを別branchで進める**。micro-stepは独立commitとして残す。

### 13.1 Branch hierarchy

- Stage branch: `stage-1-package-service-workflow`
- Step branchは、その時点のStage branch HEADから作る。
- Step完了時に対象testを通し、micro-step commitをsquashせずStage branchへ**`--no-ff`でmerge**する。fast-forwardでbranch laneを潰さない。
- 次Stepは更新済みStage branchから新しく切る。
- Stage branchから`main`へのmerge、push、PR作成は別の明示許可があるまで行わない。

Stage 1のstep branch:

1. `stage1-step01-service-contracts`
   - Service/public DTOとpackage boundaryの固定。
2. `stage1-step02-agents-workflow`
   - `agents/`と`workflow/`、`VideoQAWorkflow`、3 Taskの整理。
3. `stage1-step03-dataset-browser-runtime`
   - dataset/browser、runtime/entrypointsの責務分離。
4. `stage1-step04-records-presentation`
   - RecordService/PresentationService、Web projection/text traceの分離。
5. `stage1-step05-import-cleanup`
   - import整理、必要最小限のlegacy re-export、依存方向確認。
6. `stage1-step06-regression`
   - 全短時間回帰、compile/import、CLI/API smoke、diff check。検証で必要になったscope内修正だけcommitする。
7. `stage1-step07-remove-legacy-compat`
   - Stage 1後も残った旧compatibility packageをrepo-wide import監査後に整理・削除する。
   - 対象候補: `agent/`, `model/`, `dataset/`, `interfaces/`, `reader/`, `sampling/`。
   - 既存testを新しい公開package (`workflow/`, `agents/`, `datasets/`, `entrypoints/`, `streaming/`, `browser/`) へ移行する。
   - console script/README/現行public APIで旧pathが必要でないことを確認し、単なるtest互換のためだけに旧directoryを残さない。
   - 外部利用が実際に確認された旧importがあれば、その場で削除せず報告する。
   - `docs/file-relationships.md`, `docs/file-responsibilities.md`, `docs/processing-flow.md` を現行Stage 1構造へ更新する。存在しない旧`adapters/`, `configuration.py`, `chunking.py`, 旧top-level `pipeline.py`等を説明し続けない。

実装前preflightは変更を伴わないためbranchを切る前に行う。preflight後にStage branchを作成し、上記Step 1から開始する。

### 13.2 Micro-step commit

各Step branchでは、**1つの独立して説明・検証できる変更を1 commit**とする。例えば「Qwen backendをagentsへ移す」「SituationTaskを切り出す」「serverからRunServiceを抽出する」のように、review時に目的が一つに読める単位へ分ける。

- unrelated changeを同じcommitへ混ぜない。
- Stepの最後に巨大な一括commitを作らない。
- micro-step commit後に可能な範囲で最小testを実行する。
- Step branchをStage branchへ統合するときにsquashしない。
- commit messageは今後**日本語**で、`Stage N Step M: <タイトル>`を1行目にし、空行の後に`変更内容:` / `理由:` / `検証:`を本文として書く。必要なら`影響:`を追加する。
- Step→Stage merge commitも日本語で、`Stage N Step MをStage branchへ統合する`のように目的を明示し、本文に統合内容と検証を書く。
- このユーザー指示により、**Stage/Step branch作成とmicro-step commit作成は明示許可済み**。
- remote push、PR、Stage branchから`main`へのmergeは未許可。
- 既存Step 1--6の英語commitやlinear historyは書き換えない。この規約は**Stage 1 Step 7以降とStage 2以降**へ適用する。
- 将来Stage→mainを承認された場合も`--no-ff` mergeを基本とし、`main / Stage / Step`のbranch laneがGit Graph上で読み取れる履歴を残す。

## 14. Gate

2026-09-30 20:06 JST、ユーザーが**Stage 1を明示承認**した。blockingな未決事項はないため、本書を`approved`とする。

実装許可は**Stage 1のみ**。Stage 2（Config再設計）、Stage 3（PromptService/CRUD）、Stage 4（Dataset別user data/cache migration）はdraftのままであり、この実装へ混ぜない。実Qwen/GPU/LongVideoBench full run、model download、push/PR/main mergeも別許可。

## 15. Implementation Handoff

- approved spec: 本書
- 実装目的: 外部挙動を変えず、WorkbenchをPackage / Service / Workflow構造へ整理し、研究の一本道を短い`VideoQAWorkflow`から読めるようにする。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `2b5f8309ed380951d812c3f2191f57ce30fb7ccd`（GitHub remote main、実装着手時にlocal/remoteを再確認）
- 変更scope: Section 2--10に加え、Section 13のStage 1 Step 7 legacy compatibility cleanupまで。
- 対象外・維持条件: Section 8--9。特にConfig schema、Prompt CRUD、Dataset別storage migration、scientific behaviorは変更しない。
- success criteria: Section 11。
- 許可されている短時間検証: unit/Fake/browser既存回帰、compile/import、CLI/API smoke、diff check。GPUを必要としない範囲。
- 長時間runの許可状態: 未許可。
- Git操作: Section 13のStage/Step branch作成、micro-step commit、Step→Stageのlocal統合は明示許可済み。push/PR/Stage→main mergeは未許可。
- 未検証予定: 実Qwen/GPU、LongVideoBench実データ、長尺/科学的性能。


## 16. Implementation Evidence（2026-10-01）

GitHub上のWorkbench `main` でStage 1完了を確認した。

- merge commit: `0bd883a3ea45d88f2a219ea582d6e989ed2813bb`
- Step 7 commit: `4344f81e`
- Step 7 merge: `175416ad`
- 旧compatibility package `agent/`, `model/`, `dataset/`, `interfaces/`, `reader/`, `sampling/` は削除済み。
- 現行package: `agents/`, `workflow/`, `datasets/`, `streaming/`, `browser/`, `runtime/`, `records/`, `presentation/`, `entrypoints/`。
- Step 7 commit message記録では184 tests passed、compileall、公開package import、CLI help、editable console script smoke、`git diff --check`を実施済み。
- 実Qwen/GPU/LongVideoBench実データはStage 1の検証対象外のまま。

以上により本specの必須実装・短時間検証は完了し、`implemented`とする。
