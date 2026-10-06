---
date: 2026-10-06
project: agentic-streaming-videoqa
source_todo: "Workbenchのコード構造・ディレクトリ責務を理解し、リファクタリング方針を壁打ちする"
topic: workbench-current-architecture-audit
status: exploratory
tags: [brainstorm, refactor, architecture, workbench, service, workflow]
---

# Workbench現行コード構造の再確認とリファクタリング壁打ち

## 2026-10-06 23:08 JST 時点

### 目的

新しいSituation / Summary / Answerの最小3 Agent案へ移る前に、Workbench `main` の現行処理経路・責務・依存を再確認し、削除やspec化を急がず「何がどこで行われているか」を説明できる状態にする。

確認対象:
- `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main`
- HEAD: `85bdda340e2609cc7c9525208c436b8b05ed6218`
- Company project README / 2026-09-30 package-service-workflow spec / 2026-10-02 deterministic Evidence time関連 / 2026-10-06 three-agent-contract-simplification
- Notion「MTG議事録」の2026-10-02周辺と現在のAgent入出力整理

## 確認済みの現行研究フロー

概念上の一本道は次。

```text
QuestionSample
  -> VideoWindow stream
  -> SituationTask
  -> Situation validation
  -> MemoryTask
  -> Memory validation / narrative update
  -> 次window
  -> EOF
  -> AnswerTask
  -> Answer validation
  -> RunRecord
  -> Presentation
```

`workflow/video_qa.py` の `VideoQAWorkflow` がこの順序を監督し、`AgentTeam` は `SituationTask / MemoryTask / AnswerTask` の集合を保持する。AgentTeam自身は動画進行stateを持たない。

### 現行Agent

- Situation: `run_chunk_understanding` / `SituationTask`
  - Question、window metadata、frame manifest、optionally previous narrativeをPromptへ入れる。
  - video_clipではvideo_framesとsample_fpsをModelRequestへ渡す。
  - video raw JSONはwindow_summary / observations / unresolved。
  - Evidence時刻は現在はBackendがevidence_frame_indicesからactual timestampを決定的に導出する。
- Memory: `run_evidence_aggregation` / `MemoryTask`
  - Question、validated Situation、previous evidence/narrative、frame manifestを使う。
  - text-only model call。
  - events / narrative / unresolvedを生成する。
  - event時刻もEvidence refsからBackend導出。
- Answer: `run_final_answer` / `AnswerTask`
  - EOF後だけ実行。
  - Question / Choices / final memory contextから回答する。
  - video modeではevent/frame/timestamp/narrative versionまで検証する。

## Current memory budget

`memory_budget_tokens` はAgentの `max_new_tokens` とは別。
現行 `workflow/memory.py::fit_narrative_to_budget` が、Memory Agent生成後のnarrativeをtoken budget超過時にBackend側で機械的に圧縮する。
defaultはSituation 1024 / Memory 768 / Answer 384 max_new_tokens、memory budget 6000。

## Package責務

- `core/`: 共通DTO、StageName、ModelRequest/Response、Protocol、registry、共通validation。
- `config/`: canonical Config解決、runtime override、Agent別model/prompt/generation解決。
- root `configs/`: default YAML / recipes。
- `prompts/` package: Prompt Libraryの永続化・version・hash・互換性検証。
- root `prompts/`: built-in Prompt asset。
- `datasets/`: dataset adapterとQuestionSample取得。
- `streaming/`: sequential reader、sampling、VideoWindow stream。
- `agents/`: generic Agent wrapper、Qwen/Fake backend、ModelPool。
- `workflow/`: 3 Task、AgentTeam、VideoQAWorkflow、role固有validation。
- `records/`: machine artifactの保存・読取。
- `presentation/`: recordsからWeb view/text traceを決定的に投影。
- `browser/`: dataset catalog/search/library/media/translation。
- `storage.py`: WORKBENCH_HOME、Dataset別library/cache、settings storage。
- `runtime/`: 本来run/session lifecycle境界。
- `entrypoints/`: CLI/HTTP入口。
- `web/`: static browser UI。

## Service境界の実装実態

Service自体の存在より、CLI経路とWeb経路で使われ方が揃っていないことが現在の理解難易度につながっている。

### CLI

`entrypoints/cli.py` は:
- ConfigService
- DatasetService
- VideoStreamService
- ModelPool
- RecordService
- VideoQAWorkflow

を比較的明示的に組み合わせる。

### Web

`entrypoints/server.py` 内の `ServerContext` が:
- Config / Prompt
- Dataset registry
- Browser / media / translation
- RunRecord
- stream生成
- ModelPool
- TurnSession
- Presentation
- run lifecycle

をまとめて保持する。

さらに、
- `runtime/service.py` の `RunService` は `entrypoints.server.ServerContext` を生成し、ほぼ全メソッドを転送する。
- `runtime/session.py` は `entrypoints.server.TurnSession` をimportして再exportする。
- `ServerContext.start_run` は `DatasetService`, `VideoStreamService`, `RecordService` を使わず、registry dataset、`configured_window_stream`、`RunRecord.create` を直接利用する。
- modern Agent設定経路では `ModelPool.for_settings` -> `AgentTeam.from_models` -> `Agent(...)` となり、`AgentService` は主要Web/CLI経路の中心ではない。

このため、docs/spec上の
```text
entrypoints -> runtime -> workflow
```
という一方向境界は、現在のコードでは完全には成立していない。

## 現行Webの実行経路

```text
Browser UI
  -> collectSettings()
  -> POST /api/recipe/preview
  -> settings_from_runtime_mapping()
  -> ConfigService.resolve()
  -> POST /api/runs
  -> RunService (facade)
  -> ServerContext.start_run()
  -> QuestionSample取得
  -> configured_window_stream()
  -> ModelPool.for_settings()
  -> TurnSession
  -> POST /api/runs/<id>/turns/next
  -> TurnSession.advance()
  -> VideoQAWorkflow.process_window()
  -> Situation -> Memory
  -> RunRecord
  -> PresentationService.web_view()
  -> Browser表示
```

EOF時はTurnSessionが `VideoQAWorkflow.answer_at_eof()` を呼ぶ。

## 研究コアと周辺基盤

研究コア:
- `workflow/video_qa.py`
- `workflow/team.py`
- `workflow/situation.py`
- `workflow/memory.py`
- `workflow/answer.py`
- role固有validator
- Agent Prompt / Agent Config
- `agents/qwen3_vl.py` のModelAdapter境界

周辺基盤:
- Dataset browser / library / cache / translation
- HTTP routing / static assets
- Config persistence / Prompt CRUD
- Run/session lifecycle
- Streaming reader/sampling
- Record persistence
- Presentation projection

## 現時点の解釈

責務分離が効いている:
- Dataset固有処理とBrowser機能の分離。
- streaming reader/samplingとWorkflowの分離。
- Qwen固有generate処理と研究Taskの分離。
- Record(machine SSOT)とPresentation(read-only projection)の分離。
- ConfigとPrompt Libraryの分離。
- AgentTeamとVideoQAWorkflowの概念分離。

複雑化している:
- `entrypoints/server.py` が約1112行で、HTTP入口だけでなくapplication/runtime orchestrationを抱える。
- runtimeがentrypointsへ依存しており、本来意図した依存方向と逆。
- RunServiceはServerContextの薄いforwarderで、境界として責務を移せていない。
- DatasetService / VideoStreamService / RecordService / AgentServiceがWeb経路で一貫して使われず、Serviceあり/なしの二重の読み方が生じている。
- Workflowは研究フローを集約できているが、Memory event ledger、Evidence chain、backend compaction等により新しい最小3 Agent案より責務が重い。

## 新3 Agent案との接続

別brainstorm `2026-10-06-three-agent-contract-simplification.md` の有力案:
- Situation: current video only -> situation_description
- Summary: previous_summary + situation_description -> summary
- Answer: question + choices + summary -> answer (EOF only)

この方向では `AgentTeam = 能力の集合`, `VideoQAWorkflow = 実行順・state` という現在の概念分離は残せる可能性が高い。
一方、現行のStageName、Task名、Evidence/event validators、memory artifact、insufficient_evidence判定、Backend compaction、UI researcher viewは差分調査が必要。

## 未決事項

- Serviceを「公開境界」として全経路で徹底して使うか、薄いServiceは廃して直接依存を単純化するか。
- TurnSession / ServerContextをruntimeへ実体移動し、entrypoints/server.pyをHTTP routingだけにするか。
- 新3 AgentではTaskという語を残すか、SituationAgent / SummaryAgent / AnswerAgent自体をI/O契約を持つ実行単位とするか。
- Input / Output dataclassをどの層へ置くか。
- 新run artifactをSituation/Summary/Answer中心へ単純化しつつ、旧runをread-only表示する境界。
- Browser UI外観を保ったまま、Memory/event/evidence依存表示をどう置換するか。

## 次の壁打ち候補

次は削除判断ではなく、現在の各主要fileを「研究コア / application orchestration / infrastructure / UI」に色分けし、依存矢印を簡略図にしたうえで、各Serviceについて
1. 境界として価値がある
2. 薄いが将来差替え点として残す価値がある
3. 単なるforwardingで理解コストだけ増やしている
のどれかを一緒に判定する。
