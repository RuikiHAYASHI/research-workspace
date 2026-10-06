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


## 2026-10-07 00:23 JST 追記 — HTTP / ServerContext / Service入口の理解整理

### HTTPとWeb UI

`web/app.js` はブラウザ上で動くJavaScriptであり、Pythonの研究処理を直接呼び出せない。
そのためHTTPを介して `entrypoints/server.py` に要求を送る。

例:

```text
JavaScript object
  -> JSON.stringify()
  -> HTTP POST
  -> server.py
  -> JSON parse
  -> Python object / dict
  -> Service / Python処理
  -> Python dict
  -> json.dumps()
  -> HTTP response
  -> response.json()
  -> JavaScript object
```

JSONはJavaScriptそのものではなく、JavaScript・Python間で共有できるデータ表現形式。

### `/api/recipe/preview` の意味

`/api/recipe/preview` はファイルやディレクトリではなくHTTP endpoint。
`web/app.js` が `POST /api/recipe/preview` を送ると、`server.py` の `do_POST()` がpathを判定し、`context.preview(settings)` を呼ぶ。

用途はrun作成前の設定検証・解決済みPrompt/Question/Choices等のpreview。
run開始時にもvalidationされるため、previewは主にUX上の事前確認であり、推論実行そのものではない。

### `ServerContext` の実態

`ServerContext` は `entrypoints/server.py` にあるdataclass。
現在はServiceや共有状態を保持するだけでなく、
- Dataset取得
- stream生成
- Record作成
- ModelPool利用
- TurnSession生成
- run lifecycle
- Browser / media / translation
- settings / prompt周辺
などの実処理・調停まで担っている。

したがって名前はContextだが、実態は「共有情報の保持 + application orchestration + run管理」が混在している。

### RunServiceとproxy

現行 `runtime/service.py::RunService` は本体処理を持たず、
`ServerContext.start_run()`, `start_next_turn()` などへforwardする。
さらに `__getattr__` によりRunServiceにない属性・メソッドもServerContextへ転送する。

この意味で現在のRunServiceは「ServerContextへの代理窓口(proxy)」であり、Service自体が責務の本体になっていない。

### Serviceを正式な入口にする方向

現在の壁打ちでは、次を有力方向とする。

- Datasetを利用する正式入口: DatasetService
- VideoWindow生成の入口: VideoStreamService
- Config解決の入口: ConfigService
- Prompt管理の入口: PromptService
- Run lifecycleの入口: RunService
- Record永続化の入口: RecordService
- 表示用projectionの入口: PresentationService
- Dataset browsingの入口: BrowserService

`entrypoints/server.py` はHTTP request/response変換だけを担当し、研究処理・Dataset・Recordの詳細を知らない形を目指す。

概念:

```text
Browser (web/app.js)
  -> HTTP
entrypoints/server.py
  -> Service
  -> domain / workflow
  -> Service result
entrypoints/server.py
  -> JSON / HTTP
Browser
```

### ServiceContainer案

ServerContextの代わりに、Serviceをまとめて保持するだけの `ServiceContainer` を置く案が有力。

```text
ServiceContainer
├─ ConfigService
├─ PromptService
├─ DatasetService
├─ VideoStreamService
├─ AgentService
├─ RunService
├─ RecordService
├─ PresentationService
└─ BrowserService
```

`AppContext` という名前も候補だが、Service以外のpath/state/environmentまで何でも入れやすく、現在のServerContextのように巨大化する危険がある。
今回の「Serviceを入口にする」という意図には `ServiceContainer` の方が責務を明示しやすい。

重要なのは、ServiceContainerを「全データの中継地点」にしないこと。
ContainerはServiceを組み立て・保持する場所であり、実処理は各Serviceが担う。

例:

```text
server.py
  -> services.runs.start_run(...)

RunService
  -> DatasetService
  -> VideoStreamService
  -> Agent / Model boundary
  -> VideoQAWorkflow
  -> RecordService
```

### 保存情報の単純化方向

新しいSituation / Summary / Answer構成に合わせ、新run artifactは現在のObservation/Event/Evidence中心から単純化したい。

現時点の最小候補:

```text
run/
├─ execution settings
├─ resolved prompts
├─ run status
├─ window/frame metadata
├─ Situation description per window
├─ Summary per window
├─ model execution metadata / raw output（研究再現に必要な範囲）
└─ final answer
```

現行の `memory.jsonl`, event ledger, certainty, importance, unresolved, evidence chain等を新runでも残す必然性は再検討する。
旧run互換は新しい研究契約を複雑化させず、必要ならlegacy/read-only境界で扱う方向。

### 現在の方向性

有力:
- Serviceを機能ごとの正式入口にする。
- `server.py` をHTTP境界へ縮小する。
- `RunService` をproxyではなくrun管理の本体へする。
- `ServiceContainer` をServiceの組立・保持だけに使う。
- Dataset/Streaming/Recordなどへの直接アクセス経路を整理し、CLI/Webで同じService境界を利用する。
- 新3 Agentに合わせて保存artifactを単純化する。

まだ未決:
- ServiceContainerの具体的な所有関係・生成場所。
- AgentServiceとModelPoolをどう整理するか。
- TurnSessionをRunService内部実装にするか独立runtime objectにするか。
- Recordファイル構成の具体名。
- PresentationServiceとBrowserServiceがRecordServiceをどう読むか。


## 2026-10-07 00:30 JST 追記 — 要約版（現在構造 / 問題点 / 理想構造）

### 現在の構造

Workbenchは大きく、Browser（ブラウザ画面）とPython実行系に分かれる。

```text
Browser
  web/app.js
      |
      | HTTP（ブラウザとPythonの通信）
      | JSON（通信で使うデータ形式）
      v
entrypoints/server.py
      |
      | 現在はHTTP受付だけでなく
      | Run管理・Dataset取得・Streaming・Record等も担当
      v
ServerContext
      |
      +-- Dataset / Streaming / Model / Record / Browser / Presentation
      |
      v
TurnSession
      |
      v
VideoQAWorkflow
      |
      +-- Situation
      +-- Memory
      +-- Answer
```

- `web/app.js`: Browser側のUI制御。設定を集め、HTTPでPythonへ送り、返ってきたJSONを画面へ表示する。
- `entrypoints/server.py`: ローカルWebサーバー。HTTP request（要求）を受ける。
- `ServerContext`: 現在はServiceや共有状態の保持に加え、Run開始・Dataset取得・Streaming生成・Record生成なども担う。
- `RunService`: 現在は処理本体ではなく、ほぼ `ServerContext` へ処理を転送するproxy（代理窓口）。
- `TurnSession`: Webで1 windowずつ進めるための実行状態を保持する。
- `VideoQAWorkflow`: Situation -> Memory -> ... -> EOF -> Answer という研究上の処理順序を管理する。

CLI（コマンドライン実行）ではDatasetService / VideoStreamService / RecordService等を比較的明示的に利用する一方、WebではServerContextから内部実装を直接呼ぶ経路がある。

### 現在の問題点

本質的な問題は「Serviceが多いこと」ではなく、**Serviceが正式な入口として統一されていないこと**。

例:

```text
Dataset

CLI:
DatasetService
  -> DatasetAdapter

Web:
ServerContext
  -> registry.dataset(...)
  -> DatasetAdapter
```

Datasetを読む処理自体を二重実装しているわけではないが、「Datasetを使うとき、DatasetServiceを通るのか直接Adapterを呼ぶのか」が統一されていない。

StreamingやRecordも同様。

この結果、

- 正式な入口が分かりにくい。
- CLIとWebで処理経路が違う。
- `RunService` という名前なのにRun管理の本体は `ServerContext`。
- `runtime` が `entrypoints/server.py` に依存し、依存方向が直感と逆。
- `server.py` がHTTP境界以上の責務を持ち、巨大化している。
- 新しくコードを読む人が「どこから追えばよいか」迷いやすい。

### 理想とする構造案

Service（サービス）を各機能の正式な入口にする。

```text
Browser
  web/app.js
      |
      | HTTP + JSON
      v
entrypoints/server.py
      |
      | HTTP <-> Python の変換だけ
      v
ServiceContainer
      |
      +-- ConfigService
      +-- PromptService
      +-- DatasetService
      +-- VideoStreamService
      +-- AgentService / Model boundary
      +-- RunService
      +-- RecordService
      +-- PresentationService
      +-- BrowserService
```

`ServiceContainer` はServiceをまとめて保持するだけの箱とする。
全データを中継したり、Run処理そのものを実行したりしない。

Run開始は次のようにする。

```text
server.py
  -> RunService.start_run()
       |
       +-- DatasetService
       +-- VideoStreamService
       +-- Agent / Model
       +-- VideoQAWorkflow
       +-- RecordService
```

これにより、

- Datasetを使うならDatasetService
- StreamingならVideoStreamService
- Run管理ならRunService
- 保存ならRecordService
- 表示用変換ならPresentationService

と、機能ごとの入口が一意になる。

### ServiceContainerという名前を使う理由

`AppContext`（アプリ全体の共有文脈）という名前も可能だが、Path・State・Environmentなど何でも入れやすく、巨大化しやすい。

`ServiceContainer` なら「Serviceを入れる箱」という責務が名前から明確で、今回の目的に合う。

### 新3 Agentと保存情報

研究コアはSituation / Summary / Answerへ単純化する方向。

```text
window 0
  -> SituationAgent
  -> SummaryAgent

window 1
  -> SituationAgent
  -> SummaryAgent

...

EOF
  -> AnswerAgent
```

保存情報も現在のObservation / Event / Evidence中心から単純化し、

```text
run/
  - execution settings
  - resolved prompts
  - run status
  - window / frame metadata
  - situation_description per window
  - summary per window
  - model実行情報（研究再現に必要な範囲）
  - final answer
```

程度を中心にする案が有力。

### 今回出た主な質問

- `web/app.js` は何をしているのか。
- `entrypoints/server.py` は何をしているのか。
- HTTPとは何か。
- `runtime/service.py` は何をしているのか。
- `entrypoints/server.py` が各Serviceを呼んでいるのか。
- `agents/Agent` は何をしているのか。
- `records/` はどこに何を保存しているのか。
- 新3 Agent実装後はどのようなRecord構造が期待されるか。
- `POST /api/recipe/preview` はなぜ実行されるのか。
- `/api/recipe/preview` はどこに存在するのか。
- BrowserからPythonコードをどのように呼び、出力をどう受け取るのか。
- `ServerContext` とは何か。クラスなのか。
- 「ServerContextへのproxy」とは何か。
- CLIとWebの違いは何か。
- Dataset / Streaming / Recordの処理をServerContext側で重複実装しているのか。
- JavaScript（JS）とJSONの関係は何か。
- この文脈でserverを日本語でどう理解すればよいか。
- `ServiceContainer` と `AppContext` の違いは何か。


## 2026-10-07 00:40 JST 追記 — Service間フローと実行管理責務

### 新たな論点

Serviceを各機能の正式入口にすると、別途「どのServiceを、いつ、どの順番で呼ぶか」というapplication-level orchestration（アプリケーション全体の実行調停）が必要になる。

この責務を `ServerContext` に戻すと再び巨大化するため、現時点では `RunService` を実行管理の中心にする案が有力。

### 役割分担の候補

- `ServiceContainer`: Serviceを生成・保持するだけ。実行順序を持たない。
- `RunService`: 1回のRunの開始・進行・終了・取消を調停する。Dataset / Stream / Model / Record / Workflowを接続する。
- `RunSession`（現TurnSession相当）: Webの途中状態を保持する。current turn、stream iterator、EOF、cancel等。研究ロジックは持たない。
- `VideoQAWorkflow`: Situation -> Summary -> ... -> EOF -> Answer という研究上の順序・研究stateを担当する。HTTPやBrowser事情を知らない。
- 各Service: 自分の専門機能だけを提供する。

概念:

```text
ServiceContainer
  |
  +-- ConfigService
  +-- PromptService
  +-- DatasetService
  +-- VideoStreamService
  +-- Agent/Model service
  +-- RecordService
  +-- PresentationService
  +-- BrowserService
  +-- RunService
          |
          +-- RunSession
          |
          +-- VideoQAWorkflow
```

### Serviceの仕事とRun時の流れ

```text
1. ConfigService
   UI/Config入力をExecutionSettingsへ解決
   PromptServiceからPromptも解決

2. RunService.start_run()
   DatasetServiceからQuestionSample取得
   VideoStreamServiceでVideoWindow streamを開く
   Agent/Model境界からModelを用意
   RecordServiceでRunRecordを作る
   VideoQAWorkflowを作る
   RunSessionへ実行途中stateを保持

3. RunService.advance()
   RunSessionから次のVideoWindowを取得
   VideoQAWorkflowへ渡す
      -> SituationAgent
      -> SummaryAgent
   RecordServiceへ必要情報を保存
   EOFならAnswerAgentを実行

4. PresentationService
   保存済みRecordをBrowser表示用データへ変換

5. server.py
   Serviceの返り値をJSON化してBrowserへ返す
```

BrowserServiceは推論Runの途中には基本的に参加せず、「何を実行するか選ぶ」前段を担当する。

### CLIとWebの統一候補

同じRunService APIを利用し、進め方だけ変える。

```text
Web:
start_run()
advance()  # 1回だけ
ユーザー操作
advance()

CLI:
start_run()
while not done:
    advance()
```

これによりDataset / Streaming / Record / Workflowへの入口はCLIとWebで共通化できる。

### 未決

- RunServiceとRunSessionの具体的なファイル配置・名称。
- scientific state（Summaryなど）をWorkflow自身が持つか、RunSessionが保持してWorkflowへ渡すか。
- Record書き込みをWorkflowが直接行うか、RunServiceがWorkflow結果を受けてRecordServiceへ渡すか。
- ModelPool / AgentServiceを独立Serviceとして残すか。


## 2026-10-07 00:50 JST 追記 — Workflow / RunSession / Record の責務分離

ユーザー意向として、RunSessionはあくまで「実行役」とし、Agentへの入力構築やSituation/Summary/Answer間の研究ロジックはVideoQAWorkflowへ寄せる方向が有力。

### 有力な責務分担

```text
RunService
  -> RunSessionを作成・管理

RunSession
  -> 次のwindowを取得
  -> VideoQAWorkflowへ渡す
  -> WorkflowResultを受け取る
  -> RecordServiceへ保存を依頼
  -> EOF / cancel / current turn等の実行状態を管理

VideoQAWorkflow
  -> Agent入力を構築
  -> SituationAgentを実行
  -> SummaryAgentを実行
  -> research state（例: current_summary）を更新
  -> EOF時にAnswerAgentを実行
  -> 保存非依存のWorkflowResultを返す

RecordService
  -> WorkflowResult / Run metadataを永続化
```

### 境界の考え方

- RunSessionは「何を実行したか」を管理するが、「Agentへ何を入力するか」は知らない。
- VideoQAWorkflowは研究契約とAgent間データフローを知るが、HTTP / Browser / ファイル保存方式を知らない。
- RecordServiceは研究ロジックを知らず、渡された結果を保存する。
- current turn, EOF, cancel, stream iteratorなどはRunSession側。
- current_summaryなど研究意味を持つstateはWorkflow側に置く案が自然。

### 期待するstep flow

```text
RunSession.advance()
  -> next(video_window)
  -> workflow.process_window(video_window)
       -> build SituationInput
       -> SituationAgent
       -> build SummaryInput
       -> SummaryAgent
       -> update workflow state
       -> WindowWorkflowResult
  -> record_service.save_window_result(...)
  -> update run execution state
```

EOF:

```text
RunSession.advance()
  -> EOF
  -> workflow.finish()
       -> build AnswerInput
       -> AnswerAgent
       -> FinalWorkflowResult
  -> record_service.save_final_result(...)
  -> mark run completed
```

これにより、Workflow単体をRecordなしでtestでき、CLI/Web/将来の実験runnerから同じ研究ロジックを再利用しやすくなる。


## 2026-10-07 統合要約

Serviceを正式な入口にし、ServiceContainerはService保持、server.pyはHTTP境界、RunServiceはRun全体管理、RunSessionは1 step実行、VideoQAWorkflowはAgent入力生成・Situation/Summary/Answer・research state、RecordServiceは保存を担当する方向が有力。Workflowは保存せずResultを返し、RunSessionがRecordServiceへ保存を依頼する。CLI/Webは同じRunService/RunSession/Workflowを使い、advanceを誰が呼ぶかだけを変える。新run artifactはSituation/Summary/Answer中心へ単純化する。
