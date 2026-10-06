---
date: 2026-10-07
last_updated: 2026-10-07
project: agentic-streaming-videoqa
type: implementation
status: draft
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 85bdda340e2609cc7c9525208c436b8b05ed6218
source_brainstorm:
  - 2026-10-06-three-agent-contract-simplification.md
  - 2026-10-06-workbench-current-architecture-audit.md
related_specs:
  - 2026-09-30-workbench-package-service-workflow-refactor-spec.md
  - 2026-09-30-workbench-agent-workflow-config-spec.md
  - 2026-10-01-workbench-run-results-researcher-view-spec.md
---

# Workbench Runtime / Workflow / Record 簡略化 spec

## 1. 目的

現行Workbenchは、2026-09-30のPackage / Service / Workflow refactorを経て主要packageは分離された一方、現在の実装では以下が残っている。

- `runtime.RunService` が `entrypoints.server.ServerContext` を包むproxyになっており、依存方向が `runtime -> entrypoints` へ逆転している。
- Web経路では `ServerContext` がDataset / Streaming / Model / Record / Session / Presentationを直接調停し、CLI経路とService利用方法が揃っていない。
- `VideoQAWorkflow` がSituation / Memory / Answerの研究ロジックに加えてRecord書き込みまで担当している。
- 現行Situation / Memory / Answer契約はEvidence、Event、certainty、unresolved、narrative version等を含み、最小Streaming VideoQA baselineとして複雑である。
- Recordが `chunks.jsonl`, `stages.jsonl`, `memory.jsonl`, `memory.json`, `turns.jsonl` 等へ分散している。
- `SituationTask / MemoryTask / AnswerTask`、generic `Agent`、`AgentService`、`ModelPool` 等の名前と実責務が一致していない。

本specでは、**Serviceを各機能の正式入口へ統一し、Runtimeの実行管理、VideoQAの研究ロジック、Record永続化を明確に分離する。同時に研究コアをSituation / Summary / Answerの最小3-Agent baselineへ置き換え、新Run artifactを単純化する。**

最終状態では、コードを読む人が以下の規則だけで追跡先を判断できることを目標とする。

```text
外部通信       -> entrypoints
Service保持    -> ServiceContainer
Run全体管理    -> RunService
1 Runの実行    -> RunSession
研究ロジック   -> VideoQAWorkflow
Agent能力      -> AgentTeam
保存           -> RecordService
表示           -> PresentationService
```

---

## 2. Authority / 既存specとの関係

本specは、現行 `main@85bdda340e2609cc7c9525208c436b8b05ed6218` を基準とする。

以下の既存specは実装済みまたは承認済みであるが、本specと競合する契約については本specを新しい契約とする。

- `2026-09-30-workbench-package-service-workflow-refactor-spec.md`
  - Service / Workflow分離の考え方は維持する。
  - `VideoQAWorkflow` がRecord書き込みまで監督する契約は置き換える。
  - Stage/Step branchを多数作るGit運用は本specでは採用しない。
- `2026-09-30-workbench-agent-workflow-config-spec.md`
  - ConfigServiceをcanonical入口とする考え方は維持する。
  - `memory` top-level config、`agents.memory`、`memory_budget_tokens`、`observation_context_mode` は新Run契約から削除する。
- `2026-10-01-workbench-run-results-researcher-view-spec.md`
  - Presentationをread-only projectionとする境界は維持する。
  - 新RunではMemory/Event/Evidence中心の表示契約をSituation/Summary中心へ置き換える。
  - Legacy Runはread-onlyで旧表示を維持してよい。

旧specやbrainstormを理由に、新RunへMemory/Event/Evidence契約を再導入しない。

---

## 3. 採用する全体構造

```text
Browser / CLI
      |
      v
entrypoints
      |
      v
ServiceContainer
      |
      +-- ConfigService
      +-- PromptService
      +-- DatasetService
      +-- VideoStreamService
      +-- ModelService
      +-- RecordService
      +-- PresentationService
      +-- BrowserService
      +-- RunService
              |
              v
          RunSession
              |
              | VideoWindow
              v
       VideoQAWorkflow
              |
              +-- SituationAgent
              +-- SummaryAgent
              +-- AnswerAgent
              |
              v
        WorkflowResult
              |
              v
          RunSession
              |
              v
        RecordService
```

### 3.1 依存原則

- `entrypoints/` はHTTP / CLI入力を内部DTOへ変換し、Serviceを呼ぶ。
- `runtime/` は `entrypoints/` をimportしない。
- package外からprivate helperを直接利用せず、原則として公開Service / DTOを利用する。
- ServiceContainer全体を各Serviceへ注入しない。Serviceは必要な依存だけ明示的に受け取る。
- `VideoQAWorkflow` はHTTP、Browser、file path、JSON/JSONL保存方法を知らない。
- `RecordService` はAgent間の研究ロジックを知らない。
- `PresentationService` はread-onlyであり、表示失敗が推論結果を変更しない。

---

## 4. Runtime責務

### 4.1 ServiceContainer

配置候補:

```text
runtime/container.py
```

責務:

- application起動時に利用するServiceを保持する。
- Service間の依存を組み立てるcomposition rootとして利用する。
- Dataset取得、Run実行、Record保存などの処理自体は行わない。

想定:

```text
ServiceContainer
├─ config
├─ prompts
├─ datasets
├─ streaming
├─ models
├─ records
├─ presentation
├─ browser
└─ runs
```

実装上のprivate builder/helper名は既存styleに合わせてよい。

### 4.2 RunService

配置:

```text
runtime/service.py
```

現行の `ServerContext` proxyを廃止し、Run lifecycleの本体とする。

責務:

- resolved `ExecutionSettings` を受けてRunを開始する。
- DatasetServiceから `QuestionSample` を取得する。
- VideoStreamServiceからwindow streamを開く。
- ModelServiceから必要なModelAdapterを取得する。
- RecordServiceで新Run recordを作成する。
- AgentTeam / VideoQAWorkflow / RunSessionを組み立てる。
- `start_run / advance / restart / cancel / run_payload / run_list / thumbnail / close_all` 等、現在必要な外部操作の正式入口となる。
- active RunSessionを管理する。

RunServiceはConfig fileやHTTP JSONを直接解釈しない。Web / CLIはConfigServiceでresolved settingsを作成してからRunServiceへ渡す。

### 4.3 RunSession

配置:

```text
runtime/session.py
```

現行 `entrypoints/server.py::TurnSession` を移動・整理し、名称を `RunSession` とする。

責務:

- 1 Runを1 stepずつ進める。
- stream iteratorから次の `VideoWindow` を取得する。
- `VideoQAWorkflow.process_window()` またはEOF時の `finish()` を呼ぶ。
- WorkflowResultを受け取り、RecordServiceへ保存を依頼する。
- execution stateを管理する。
- Browserの現行thumbnail表示に必要なsession-local cacheを管理してよい。

RunSessionが保持するexecution stateの例:

- `run_id`
- `turn_index`
- window iterator / stream context
- EOF到達状態
- cancel状態
- closed状態
- thumbnail cache
- workflow参照

RunSessionは以下を知らない。

- Situation Agentへ何を入力するか。
- Summary Agentへ何を入力するか。
- current summaryをどう更新するか。
- Answer Agentへ何を渡すか。
- Record JSON/JSONLのfield構造。

---

## 5. Service境界

各機能の正式な入口を次へ統一する。

| 機能 | 正式な入口 |
|---|---|
| Config解決 | `ConfigService` |
| Prompt管理 | `PromptService` |
| Question / Dataset取得 | `DatasetService` |
| VideoWindow生成 | `VideoStreamService` |
| Model解決・再利用 | `ModelService` |
| Run lifecycle | `RunService` |
| Record保存・読取 | `RecordService` |
| 表示projection | `PresentationService` |
| Dataset Browser | `BrowserService` |

WebとCLIは同じService境界を使用する。

---

## 6. Model / Agent構造

### 6.1 generic Agent / AgentService

現行 `agents/agent.py::Agent` はroleとbackendを保持して `generate()` を転送するだけであり、新構造では削除する。

現行 `AgentService` もgeneric Agent生成の薄い窓口であるため削除する。

### 6.2 ModelService

現行 `ModelPool` の意味のある責務である、

- backend / model_idからModelAdapterを解決する。
- 同じModelを再利用する。
- Agentごとのresolved settingsから必要Modelを返す。

を正式なServiceへ整理する。

配置候補:

```text
agents/service.py
```

class名は `ModelService` を第一候補とする。新しい汎用抽象を追加する必要がなければModelPoolとの二重classを残さない。

Qwen/FakeのModelAdapter実装は `agents/qwen3_vl.py`, `agents/fake.py` に残す。

---

## 7. 新3-Agent研究契約

### 7.1 共通原則

- Modelへ不要なJSON生成を要求しない。
- Agentのsemantic outputはplain textとする。
- JSON / JSONL化はPython側で行う。
- Qwenに既知metadataを再生成させない。
- Situation / SummaryはQuestion / Choicesへ依存しない。
- AnswerはEOF時に1回だけ実行する。
- Early Answer / WAIT / Readiness判定は本spec対象外。

### 7.2 SituationAgent

旧 `SituationTask` を `SituationAgent` へ一本化する。

責務:

> 現在windowの映像だけを見て、何が起きているかを純粋に説明する。

semantic input:

```text
video_frames
sample_fps
prompt
generation
```

semantic output:

```text
situation_description: str
```

禁止:

- Question / Choicesを入力しない。
- previous summary / Memoryを入力しない。
- evidence_frame_indices等を生成させない。
- certainty / unresolved / question_relevance等を生成させない。

### 7.3 SummaryAgent

旧 `MemoryTask / MemoryAgent` を削除し、`SummaryAgent` へ置き換える。

責務:

> 直前までの累積Summaryと現在windowのSituation descriptionを統合し、更新済みSummaryを返す。

semantic input:

```text
previous_summary
situation_description
prompt
generation
```

semantic output:

```text
summary: str
```

初回windowでは `previous_summary=""` を許容し、Prompt側で初回として扱う。

禁止:

- Question / Choicesを入力しない。
- events / event_id / importance / certainty / unresolvedを生成させない。
- Evidence chainを作らない。
- `narrative` という新Run用名称を使わない。

### 7.4 AnswerAgent

旧 `AnswerTask` を `AnswerAgent` へ一本化する。

責務:

> EOF時にQuestion / Choices / 最終Summaryから最終回答を選択する。

semantic input:

```text
question
choices
summary
prompt
generation
```

Model semantic output:

```text
<1-based choice number>. <choice text>
```

例:

```text
2. He puts the glass on the table.
```

Python側で以下を決定的に検証する。

- 先頭のchoice numberが1..N内である。
- numberが指すchoice textと出力本文が一致する、またはcanonical choice textへ正規化可能である。
- invalid outputはvalidation errorとし、存在しない回答を補完しない。

旧Evidence event/frame/timestamp/narrative version検証は新Runから削除する。

---

## 8. Agent / Workflow dataclass

### 8.1 Agent固有型

各Agent固有のInput / Outputは対応fileの近くに置く。

```text
workflow/
├─ situation.py
│   ├─ SituationInput
│   ├─ SituationOutput
│   └─ SituationAgent
├─ summary.py
│   ├─ SummaryInput
│   ├─ SummaryOutput
│   └─ SummaryAgent
└─ answer.py
    ├─ AnswerInput
    ├─ AnswerOutput
    └─ AnswerAgent
```

semantic field名はSection 7を契約とする。

Modelのraw output、model info、elapsed time等のexecution metadataは、Recordへ渡せる形でAgent OutputまたはWorkflow Resultに保持する。privateな共通helperの有無は実装判断でよいが、単一用途の新しい汎用抽象を増やさない。

### 8.2 Workflow横断型

複数Agentをまたぐ型は `workflow/contracts.py` へ置く。

最低限:

- `WindowWorkflowResult`
  - `window`
  - Situation result
  - Summary result
- `FinalWorkflowResult`
  - Answer result

現行 `StageResult / WindowTurnResult / PipelineResult` が新契約で不要になれば削除する。互換のためだけに残さない。

---

## 9. AgentTeam

`AgentTeam` は維持する。

```text
AgentTeam
├─ situation: SituationAgent
├─ summary: SummaryAgent
└─ answer: AnswerAgent
```

AgentTeamの責務は「利用可能なAgent能力の集合」だけとする。

Agent間の入力接続・実行順・state更新はVideoQAWorkflowが担当する。

---

## 10. VideoQAWorkflow

`VideoQAWorkflow` は研究ロジックだけを担当する。

### 10.1 WorkflowState

明示的なresearch stateを持つ。

初期版:

```text
WorkflowState
└─ current_summary: str
```

`turn_index / EOF / cancel / stream iterator` をWorkflowStateへ入れない。

### 10.2 process_window

概念フロー:

```text
VideoWindow
    |
    v
SituationInputを構築
    |
    v
SituationAgent
    |
    v
SituationOutput.situation_description
    |
    +------------------------+
    |                        |
previous current_summary     |
    |                        |
    +----------+-------------+
               v
        SummaryInputを構築
               |
               v
         SummaryAgent
               |
               v
         SummaryOutput.summary
               |
               v
WorkflowState.current_summaryを更新
               |
               v
     WindowWorkflowResult
```

`process_window()` はRecordへ書き込まない。

### 10.3 finish

EOFで1回だけ呼ぶ。

```text
QuestionSample.question
QuestionSample.choices
WorkflowState.current_summary
          |
          v
     AnswerInput
          |
          v
      AnswerAgent
          |
          v
 FinalWorkflowResult
```

旧 `event_count == 0 -> insufficient_evidence` 判定は削除する。

windowが1件も正常処理されずsummaryが存在しない場合は、存在しないEvidenceを補わず明示的な実行errorとする。

### 10.4 Record非依存

以下をWorkflowから削除する。

- `RunRecord` 参照。
- `record.append_*`。
- status update。
- Presentation refresh。
- memory artifact読取。
- Recordを利用したprevious state取得。

---

## 11. Config契約

### 11.1 canonical default

新Configは `memory` top-level fieldを持たない。

第一候補:

```yaml
dataset:
  adapter: longvideobench
  data_root_name: longvideobench

streaming:
  window_seconds: 4
  frames_per_window: 8
  reader_mode: target_only
  visual_input_mode: video_clip
  decoder_frames_per_sample: 16

agents:
  situation:
    backend: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: situation.video.initial
    enabled: true
    generation:
      max_new_tokens: 1024
      temperature: 0.0

  summary:
    backend: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: summary.text.initial
    enabled: true
    generation:
      max_new_tokens: 768
      temperature: 0.0

  answer:
    backend: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: answer.text.initial
    enabled: true
    generation:
      max_new_tokens: 384
      temperature: 0.0
```

### 11.2 削除するfield

新Run / new Config pathから以下を削除する。

- top-level `memory`
- `agents.memory`
- `observation_context_mode`
- `memory_budget_tokens`
- `memory` role
- `evidence_aggregation` stage相当

Summary長はSummary Agentの `generation.max_new_tokens` で制御する。
現行 `fit_narrative_to_budget` の追加compactionは初期baselineへ持ち込まない。

### 11.3 ExecutionSettings / Prompt metadata

- Agent roleは `situation / summary / answer` とする。
- `StageName` 等の旧Memory/Evidence名称が新実行経路で不要なら削除または新roleへ置換する。
- PromptServiceの新Run compatibility判定は3 roleに合わせる。
- built-in PromptにSummary用promptを追加し、旧Memory promptを新Runで自動再利用しない。
- 既存user prompt data自体を破壊的に削除しない。旧memory-role promptは新RunのSummary promptとして自動選択しない。
- 旧browser settingsにmemory fieldが残っていても、新Runtimeへmemory契約を復活させない。必要なら無効な旧保存設定を無視・resetする最小処理とする。

---

## 12. Prompt semantic contract

正確なwordingはPrompt assetとして実装しRunへsnapshotするが、意味は以下から逸脱しない。

### Situation

- 現在windowの映像だけを説明する。
- Questionの回答を推測しない。
- 過去の内容を推測しない。
- plain textのみ。

### Summary

- `previous_summary` と `situation_description` を統合する。
- 時系列上重要な事実を保持する。
- Question/Choicesに最適化しない。
- plain textの更新済みsummaryだけを返す。

### Answer

- Question / Choices / final Summaryだけを使用する。
- choiceを1つ選ぶ。
- `<1-based number>. <exact choice text>` を返す。
- Evidence JSONを生成しない。

---

## 13. Record契約

### 13.1 新Run artifact

新Runは次を第一契約とする。

```text
<run_id>/
├─ execution_settings.json
├─ resolved_prompts.json
├─ question.json
├─ run_status.json
├─ turns.jsonl
└─ final_answer.json
```

新Run用に `chunks.jsonl / stages.jsonl / memory.jsonl / memory.json` を並行生成しない。

### 13.2 schema version

新RunをLegacy Runと決定的に区別できるよう、`run_status.json` に以下を保存する。

```json
{
  "artifact_schema_version": 2
}
```

旧Runでfieldが無い場合はlegacy schemaとして扱う。

### 13.3 execution_settings.json

resolved ExecutionSettingsのsnapshot。

新契約に存在しないmemory fieldを保存しない。

### 13.4 resolved_prompts.json

Situation / Summary / Answerで実際に使用した以下を再現可能な形で保存する。

- role
- prompt_id
- prompt_hash
- prompt_version
- prompt body
- relevant metadata

### 13.5 question.json

Run開始時のQuestionSample snapshot。

最低限:

- dataset_id
- question_id
- video_id
- video_pathまたは再識別に必要な既存field
- duration_seconds
- question
- choices

### 13.6 run_status.json

現在statusを保存する。

status値は既存Runtimeとの不必要な差分を増やさないため、原則として現行の

- `ready`
- `running`
- `awaiting_next_turn`
- `succeeded`
- `failed`
- `cancelled`

を使用する。

`insufficient_evidence` は新Runでは使用しない。

進行中Agentを記録する場合は、旧Evidence stage名ではなく `situation / summary / answer` を用いる。field名は `current_agent` を第一候補とする。

### 13.7 turns.jsonl

**1行 = 1 completed window** とする。

概念schema:

```json
{
  "turn_index": 0,
  "window": {
    "index": 0,
    "start_seconds": 0.0,
    "end_seconds": 4.0,
    "sample_fps": 2.0,
    "frames": [
      {
        "frame_index": 0,
        "timestamp_seconds": 0.0,
        "target_timestamp_seconds": 0.0
      }
    ]
  },
  "situation": {
    "situation_description": "A person picks up a glass.",
    "raw_output": "...",
    "model_info": {},
    "elapsed_seconds": 1.2,
    "prompt_id": "situation.video.initial",
    "prompt_hash": "...",
    "prompt_version": 1,
    "generation": {}
  },
  "summary": {
    "summary": "The person picked up a glass.",
    "raw_output": "...",
    "model_info": {},
    "elapsed_seconds": 0.8,
    "prompt_id": "summary.text.initial",
    "prompt_hash": "...",
    "prompt_version": 1,
    "generation": {}
  }
}
```

画像byteそのものは保存しない。Frame metadataは既存の決定的timestamp情報を保持する。

ModelAdapterの `raw_output` がJSON serializer非対応型を含む場合は、既存の安全なserializable projectionを利用するか、Record境界で決定的に変換する。

### 13.8 final_answer.json

最低限:

```json
{
  "answer": "2. He puts the glass on the table.",
  "choice_index": 2,
  "choice_text": "He puts the glass on the table.",
  "raw_output": "...",
  "model_info": {},
  "elapsed_seconds": 0.5,
  "prompt_id": "answer.text.initial",
  "prompt_hash": "...",
  "prompt_version": 1,
  "generation": {},
  "completed_window_count": 12
}
```

`choice_index` は1-basedとする。

### 13.9 保存責務

```text
VideoQAWorkflow
    -> WorkflowResult
RunSession
    -> RecordService
RecordService
    -> JSON / JSONL
```

Workflow自身はfile名/schemaを知らない。

---

## 14. Presentation / Browser

### 14.1 新Run

新RunのResearcher Viewは、各windowについて最低限以下を表示可能にする。

- Window start / end。
- Frame metadata / thumbnail（session中に利用可能な場合）。
- Situation description。
- 更新後Summary。
- 詳細表示でmodel raw output / prompt snapshot / generation / model info / elapsed time。
- EOF後のFinal Answer。

新Run UIでMemory Event / Evidence chain / certainty / importance / unresolvedを表示しない。

### 14.2 Legacy Run

既存Runはread-onlyで閲覧可能にする。

Legacy Runの旧 `chunks.jsonl / stages.jsonl / memory.jsonl / memory.json` 等を、新Run Runtimeへ取り込まない。

実装は概念的に、

```text
RecordService.open(run_id)
  |
  +-- schema v2 -> new reader
  |
  +-- schema markerなし -> LegacyRunReader
```

とする。

Legacy Runに対して以下を行わない。

- 追記。
- Resume。
- 新schemaへの自動migration。
- 新Run形式との混在保存。

Legacy表示のための最小reader / projectionだけ残す。

---

## 15. 旧実装削除方針

Git historyを過去実装の復元手段とし、backup目的の `old/`, `legacy_impl/`, `deprecated/` 等は作らない。

新経路の切替後、repo-wide import / referenceを確認し、不要になった実装file・alias・helperは積極的に削除する。

削除候補には少なくとも次を含む。

- `agents/agent.py` のgeneric Agent。
- 旧 `AgentService`。
- `workflow/memory.py`。
- `SituationTask / MemoryTask / AnswerTask` alias/旧class。
- Evidence/Event/Observation validator/helperのうち新Run・Legacy read-only表示のどちらにも不要なもの。
- `fit_narrative_to_budget`。
- 新実行経路から不要になったStageName / StageResult / memory-specific contract。
- `entrypoints/server.py` 内のServerContext / TurnSession実体。
- compatibility forwardingだけを目的とするRuntime proxy。
- 旧Record書込helper。

ただし以下は「古い実装」ではなく現在要件なので残す。

- Legacy Run read-only reader / projectionに必要な最小コード。
- 過去Prompt/Runデータそのもの。
- 新Browser / Presentationが現在利用する機能。

削除判断は「名前が旧いから」ではなく、新Runtime / new Workflow / Legacy read-onlyのいずれからも参照されないことを確認して行う。

---

## 16. Web / CLI

### 16.1 Web

HTTP route名は今回のarchitecture refactorを理由に変更しない。

少なくとも現在利用中のroute、例:

- `POST /api/recipe/preview`
- `POST /api/runs`
- `POST /api/runs/<id>/turns/next`

は維持する。

内部では、

```text
server.py
  -> ConfigService
  -> RunService
```

へ接続し、ServerContextを経由しない。

API response bodyは新Record / Presentation契約へ必要な範囲で更新してよいが、同一micro-commitでrepository同梱Browserを更新し、Browser操作を壊した状態を残さない。

### 16.2 CLI

CLIとWebで別のWorkflow実行経路を持たない。

```text
Web:
start_run()
ユーザー操作 -> advance()
ユーザー操作 -> advance()

CLI:
start_run()
while not finished:
    advance()
```

とし、どちらも `RunService -> RunSession -> VideoQAWorkflow` を利用する。

---

## 17. Resume / Restart

### 17.1 初期実装

完全なcrash-resumeは本spec対象外。

`restart` は先頭からの新しい実行として現在必要なUXを維持する。

### 17.2 将来Resume可能な保存

各completed windowの `turns.jsonl` に更新後Summaryを必ず保存する。

これにより将来、

```text
last completed turn
  -> summary取得
  -> WorkflowState(current_summary=...)
  -> next windowから再開
```

へ拡張可能にする。

将来用のresume API / checkpoint abstractionは今は追加しない。

---

## 18. 対象外

本specでは以下を実装しない。

- Early Answer / WAIT / Readiness Agent。
- 動的window長。
- multi-timescale memory。
- Situation履歴retrieval。
- Summary用の追加compaction / chapter機構。
- 完全crash-resume。
- Legacy Runのmigration / 書換え。
- Browserの大規模design変更。
- HTTP route rename。
- Dataset Browser / Library / cacheの別設計変更。
- 新dependency導入。
- 実Qwen/GPU/LongVideoBench full run。
- model download。
- mainへのmerge。
- remote push。
- Pull Request作成。

---

## 19. Compatibility

### 維持する

- BrowserからDataset / Video / Questionを選択してRunできること。
- Config / Prompt Libraryから新Runの設定・Promptを選択できること。
- `video_clip` Qwen inputとsample_fpsの既存ModelAdapter契約。
- Dataset Browser / Library / user dataの現在機能。
- Presentationはread-onlyであること。
- Legacy Runを閲覧できること。
- ローカルserverを前面起動しCtrl+Cで終了する現在運用。

### 意図的に変更する

- `Memory` role -> `Summary` role。
- new Configからmemory fieldを削除。
- Agent model outputを複雑JSONからplain textへ簡略化。
- Evidence/Event/Observation contractを新Runから削除。
- new Record artifact schemaをv2へ変更。
- new Researcher ViewをSituation/Summary中心へ変更。
- Runtime依存方向。
- CLI / Webの実行経路をRunServiceへ統一。

---

## 20. Git運用

### 20.1 Branch

実装開始時に現在の `main` / HEAD / dirty stateを確認する。

基準commitが本specの `85bdda340e2609cc7c9525208c436b8b05ed6218` から進んでいる場合は、差分を確認してstalenessを評価する。意味が変わっていなければ最新mainを基準にする。

`main` から**1本の実装branch**を作成し、そのbranch内で実装を完結させる。

推奨branch名:

```text
refactor/workbench-runtime-workflow
```

Stepごと・micro-stepごとのbranchは作らない。

### 20.2 Commit

実装branch内で、独立して説明・検証できる意味単位のmicro-commitを積む。

原則:

- 1 commit = 1つの目的として説明できる変更。
- 小さすぎる機械的commitへ分割しない。
- Agent / Runtime / Record等の異なる責務を無関係に1 commitへ混ぜない。
- 旧コード削除は新経路の参照が成立した後に行う。
- 各commit後は、その変更に最も近い短時間test / compile / smoke checkを行う。
- full短時間回帰はbranch完成時に行う。
- squash前提にしない。

### 20.3 Commit message

commit messageは日本語。

**タイトル + 本文5〜6行程度**を基本とする。

本文は箇条書きにせず文章で記述し、以下が分かるようにする。

- 何を変更したか。
- なぜ変更したか。
- どの責務・経路へ影響したか。
- 何を検証したか。

例:

```text
RunServiceとRunSessionへ実行管理を移管

ServerContextに集約されていたRun lifecycleをruntime配下へ移した。
RunServiceを公開入口、RunSessionを1 Runのstep実行役として整理した。
server.pyからDatasetやRecordの直接調停を外し、依存方向を単純化した。
関連するRuntime/APIテストとcompile checkで新しい実行経路を確認した。
```

### 20.4 Codex / 実装者に許可するGit操作

許可:

- 現在branch / HEAD / dirty state確認。
- 実装branch作成。
- 実装。
- 短時間検証。
- micro-commit作成。

禁止:

- `main`へのmerge。
- remote push。
- Pull Request作成。
- 既存commit historyのrewrite。

実装完了時のゴールは、

> **実装branchの最新commit上で、本specの要求と短時間検証が成立していること。**

main mergeとpushはユーザーが実装確認後に行う。

---

## 21. 推奨実装順

速度を優先し、Step branchは作らない。以下は実装順の目安であり、各行を必ず1 commitへ固定するものではない。意味のある動作単位を優先する。

### Step 1: Runtime boundaryを正す

- `ServiceContainer` を導入。
- `RunService` をServerContext proxyから実体へ変更。
- `TurnSession` を `RunSession` としてruntimeへ移動。
- server.pyをHTTP境界へ縮小。
- CLI/WebのRun入口をRunServiceへ寄せる。

verify:
- Runtime / API / CLIのtargeted tests。
- import / compile。

### Step 2: Model / Agent境界を整理

- ModelPool責務をModelServiceへ整理。
- generic Agent / AgentServiceを除去できる準備。
- AgentTeamを3 roleへ更新。

verify:
- Fake model / model resolution tests。

### Step 3: 3-Agent研究契約へ切替

- SituationAgent。
- SummaryAgent。
- AnswerAgent。
- Input / Output dataclass。
- WorkflowState。
- VideoQAWorkflowのSituation -> Summary -> EOF Answer。
- Question非依存Situation/Summary。
- plain text output + code-side Answer validation。
- old insufficient_evidence logic削除。

verify:
- Agent unit tests。
- 2 window以上のFake Workflow test。
- AnswerがEOFで1回だけ呼ばれること。

### Step 4: Config / PromptをSummary契約へ更新

- top-level memory削除。
- agents.memory -> agents.summary。
- observation_context_mode / memory_budget_tokens削除。
- Summary prompt追加。
- Prompt role compatibility更新。
- Browser runtime settings / saved settingsの新contract対応。

verify:
- Config / Prompt / browser settings tests。

### Step 5: Record v2 / Legacy read-only

- v2 RecordService / RunRecord。
- 6 file構成。
- `turns.jsonl`。
- `artifact_schema_version=2`。
- Legacy reader / projection。
- WorkflowからRecord書込を完全除去。
- RunSessionからRecordServiceへ保存。

verify:
- Record schema tests。
- partial final line等の既存安全性が必要なら維持。
- Legacy fixture read-only test。

### Step 6: Presentation / Browser projection

- New RunのSituation / Summary / Final Answer表示。
- model raw output / prompt / generation等の詳細表示。
- Memory/Event/Evidence UIのnew-run依存を除去。
- Legacy Runは旧projectionで閲覧。

verify:
- Presentation / API / browser tests。
- reload read-only test。

### Step 7: 旧実装削除と全体回帰

- repo-wide import/reference監査。
- 不要file / alias / helper削除。
- docs/comments/import整理は本specで変更した責務説明に必要な箇所だけ更新。
- backup directoryは作らない。

verify:
- full短時間pytest。
- compileall。
- CLI help / Fake CLI smoke。
- Fake API/browser smoke。
- `git diff --check`。
- old runtime path / Memory runtime pathへの不要参照が無いこと。

---

## 22. Success Criteria

### Architecture

1. `runtime/` が `entrypoints/` をimportしない。
2. `entrypoints/server.py` にServerContext / TurnSession実体が残らない。
3. RunServiceがRun lifecycleの本体であり、`__getattr__` proxyを持たない。
4. CLIとWebが同じ `RunService -> RunSession -> VideoQAWorkflow` 経路を利用する。
5. VideoQAWorkflowがRecord / Presentationをimportしない。
6. RunSessionがAgent入力構築を行わない。
7. ServiceContainerが実処理を持たず、各ServiceへContainer全体を注入しない。

### Research contract

8. SituationはQuestion / Choices / previous summaryを受け取らない。
9. Situation outputはplain text `situation_description`。
10. Summary inputは `previous_summary + situation_description` を中心とし、Question / Choicesを受け取らない。
11. Summary outputはplain text `summary`。
12. AnswerはEOF時に1回だけ実行する。
13. AnswerはQuestion / Choices / final summaryだけを利用する。
14. Answerのchoice number/textをPython側で決定的に検証する。
15. new RuntimeにMemory/Event/Evidence/certainty/unresolved contractが残らない。
16. `event_count == 0 -> insufficient_evidence` 判定が新Runに存在しない。

### Config

17. canonical configにtop-level `memory` が無い。
18. agentsは `situation / summary / answer` の3 role。
19. `memory_budget_tokens / observation_context_mode` が新ExecutionSettingsに無い。
20. Config / Promptだけで3 Agentのmodel / prompt / generationを確認できる。

### Record

21. new Runは原則6 file構成で生成される。
22. `run_status.json` に `artifact_schema_version=2` がある。
23. 1 completed windowにつき `turns.jsonl` 1行。
24. 各turnにwindow metadata、Situation result、Summary result、必要なmodel execution metadataがある。
25. `final_answer.json` にcanonical answer、1-based choice_index、choice_textがある。
26. new Runで `memory.json / memory.jsonl / chunks.jsonl / stages.jsonl` を生成しない。
27. Legacy Runをread-onlyで開ける。
28. Legacy Runへ追記・Resume・自動migrationしない。

### Cleanup

29. generic Agent / old AgentService / MemoryTask等、新Runtimeに不要な実装をbackup目的で残さない。
30. 削除対象はrepo-wide参照監査後に削除される。
31. Git history以外のbackup copyをrepository内に作らない。

### Regression / Verification

32. Dataset Browser / Library / Prompt Library等、本spec対象外の主要既存機能が短時間testで非回帰。
33. repository同梱BrowserでRun開始、1 step進行、EOF Answer、保存済みRun再表示がFake経路で確認できる。
34. CLIで同じFake Runが最後まで自動進行する。
35. full短時間pytest / compileall / diff checkが成功するか、環境依存failureを明確に分離して報告する。
36. 実Qwen/GPU/LongVideoBench full runを実装成功条件に含めない。

---

## 23. Ambiguity Gate

### blocking

なし。

以下は現在のユーザー指示で確定済みとして扱う。

- Modelのsemantic outputはplain textとし、JSON/JSONLはコード側で生成する。
- new Runtimeからmemory fieldを削除する。
- Recordは本specの6 file案を採用する。
- 推奨したServiceContainer / RunService / RunSession / Workflow責務分離を採用する。
- 旧実装fileはGit historyを復元手段とし、不要になれば積極的に削除する。
- Legacy Runはread-only。
- Gitは1本の実装branch + micro-commit。
- Codexはbranch作成・commitまで。
- main merge / pushはユーザーが実装完了後に行う。

### non-blocking

- private helper / private method名。
- ServiceContainer構築helperの細かい配置。
- ModelService内部cache key等、現在のModelPool挙動を保つ局所実装。
- WorkflowStateを `video_qa.py` 内に置くか将来 `state.py` へ分けるか。初期は過度にfileを増やさない。
- Legacy readerの具体class名。
- Presentation内部DTO名。
- targeted testの具体的な分割。既存test styleへ合わせる。

---

## 24. Spec Gate

本specは、これまでのbrainstormと2026-10-07のユーザー判断を実装契約へ変換した**draft**である。

blockingな未決事項は無く、内容上はapprovedへ移行可能な状態にある。

ただし `research-spec` のAuthorityルールに従い、**本spec本文をユーザーが確認し、明示承認するまではコード実装を開始しない。**

承認後:

```text
draft -> approved
```

として `engineering-task` へ引き継ぐ。

長時間run、GPU実行、push、main mergeはspec承認とは別Gateのままとする。

---

## 25. Implementation Handoff

- approved spec: 承認後、本spec
- 実装目的: WorkbenchをService入口 / Runtime実行管理 / 純粋Workflow / 単純Recordへ整理し、Situation / Summary / Answerの最小3-Agent baselineへ置き換える。
- 基準repository: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`
- 基準branch: `main`
- 基準commit: `85bdda340e2609cc7c9525208c436b8b05ed6218`（実装直前に最新mainとstalenessを再確認）
- 変更scope: Sections 3--17, 19--22
- 対象外: Section 18
- success criteria: Section 22
- 許可される短時間検証: unit / Fake / Config / Prompt / Record / Presentation / API / browser / CLI smoke / compile / diff check
- 長時間run: 未許可
- Git: 1 implementation branchの作成とmicro-commitまで許可。main merge / push / PRは禁止。
- 旧実装: 新経路切替後、不要参照を確認して積極削除。backup copyは禁止。
- 未検証予定: 実Qwen/GPU、LongVideoBench実データ、長尺科学的性能
