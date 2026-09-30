---
date: 2026-09-30
project: agentic-streaming-videoqa
source_todo: null
topic: workbench-refactor-architecture
status: exploratory
tags: [brainstorm, refactor, architecture, workbench, prompt, artifact]
---

# Workbench現行構成の理解とリファクタ候補

## 2026-09-30 17:39 JST 現在地

ユーザーはvideo_clip・Situation/Memory/Answer・text memoryの実装完了後、サーバーが現在使えないため実動作確認はせず、まず現在コードのディレクトリ構成、各責務、prompt/output形式を理解してからリファクタリングを検討したい。

確認したGitHub正本:
- `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main`
- HEAD `2b5f8309ed380951d812c3f2191f57ce30fb7ccd`
- Company spec `2026-09-30-workbench-agent-modes-and-readable-memory-spec.md` は `implemented`
- Company記録では181 tests/compile/diff checkまで完了。実Qwen/GPU/LongVideoBench実データは未検証。
- 現在サーバーを起動しての再確認は行っていないため、以下はGitHub mainの静的読解を根拠とする。

## 現行レイヤ

- `core/`: 共通dataclass、Protocol、registry、設定/prompt変数のvalidation。
- `config/`: YAML recipe/profile、prompt ID、modeごとのprompt解決、stage別generation。
- `dataset/`: LongVideoBench/Fakeの質問・catalog・検索・閲覧metadata。
- `reader/`: sequential_loaderをWorkbenchの`FrameSample/VideoWindow`へ変換し、reader modeを隠蔽。
- `sampling/`: full_rgb系で使うfirst-after-targetのtime-grid window構築。
- `agent/`: Situation/Memory/Answer、pipeline orchestration、出力JSON validation、memory budget。
- `model/`: ModelAdapter実装。Qwen3-VLのimage_list/video_clip経路とFake model。
- `records/`: run単位のJSON/JSONL保存、status、append-only memory、human-readable projection。
- `interfaces/`: CLI/HTTP server/session/browser/library(SQLite)/media/translation。
- `web/`: static frontend。
- repository rootの`prompts/en/`: prompt asset。legacyとvideo v1が共存。
- `configs/`: profile/recipe。
- `tests/`: unit/acceptance/UI。
- `docs/`: 現行運用説明。

## 主要データフロー

`Web/CLI -> settings resolver -> dataset QuestionSample -> reader VideoWindow -> Situation -> validation -> Memory -> validation -> records -> 次window -> EOF Answer -> records -> GET human view`。

video_clipでは選択済みRGB frameだけを`ModelRequest.video_frames`として1本のvideoへ渡し、`sample_fps = frame_count/window_seconds`、processorには`frames_indices=0..N-1`, `do_sample_frames=False`。元動画上のsource frame ID/actual timestampはQwen内部metadataではなくprompt manifestと`chunks.jsonl`を正本として保持。

## prompt/output

video prompt:
- `chunk_understanding_video_v1.txt`: question/window/frame manifest + video、過去memoryなし。
- `chunk_understanding_video_with_memory_v1.txt`: 上記 + previous validated narrative。
- `evidence_aggregation_video_v1.txt`: validated Situation + previous narrative + frame manifest。
- `final_answer_video_v1.txt`: question/choices + validated memory context、EOFのみ。

Situation output:
`{window_summary, observations, unresolved}`。observationsはevent/state単位で、各要素は`start_seconds,end_seconds,description,evidence_frame_indices,question_relevance,certainty`。frame数との同数制約なし。

Memory output:
`{events,narrative,unresolved}`。eventは`event_id,start_seconds,end_seconds,description,evidence_frame_indices,certainty,importance_reasons,importance_explanation`。

Answer output:
`{answer,evidence_event_ids,evidence_frame_indices,evidence_timestamps_seconds,narrative_version}`。video modeでは選択肢本文、event/frame/timestamp/versionまで検証。全windowでevent 0件ならAnswerを呼ばず`insufficient_evidence`。

主artifact:
`execution_settings.json`, `resolved_prompts.json`, `run_status.json`, `chunks.jsonl`, `stages.jsonl`, `memory.jsonl`, `memory.json`, `turns.jsonl`, `final_answer.json`。
`memory.jsonl`がappend-onlyの記憶正本、人間用timelineは`RunRecord.readable_memory()`で`chunks.jsonl + memory.jsonl`からGET時に決定生成。

## リファクタ候補（未採用）

1. **最優先候補: `agent/pipeline.py`の分割**  
   現在556行で、stage実行関数、3 Agent wrapper、AgentTeam、orchestration、mode分岐、validation、record更新が同居。  
   候補: `agents.py`（3役割）、`orchestrator.py`（window/EOF state machine）、`stage_runner.py`（prompt/model call）、schema/validatorは現行別module維持。

2. **`interfaces/server.py`の分割**  
   約937行でTurnSession、ServerContext、HTTP handler、browser/library/media/translation routeを抱える。  
   候補: `sessions.py`, `run_service.py`, `http.py`。Web/API外部契約を変えず内部のみ分離。

3. **legacy image_list と video_clip schemaの責務分離**  
   `observations.py`/`events.py`に旧・新validatorが同居し、pipeline/configにmode分岐が散る。  
   候補: schema名を型/codec単位にまとめ、mode→schema/prompt/model payloadを一つのstrategy/contractへ集約。ただし過度な抽象化は避ける。

4. **prompt resolutionの分離**  
   `config/loader.py`がYAML解決に加え、mode/contextからprompt IDを書き換える。将来prompt CRUD/Agent別modelを入れると肥大化しやすい。  
   候補: `prompt_registry.py`またはPromptPresetResolverを分離。現行runのresolved prompt/hash互換が必須。

5. **`records/run.py`のread/write/view分離**  
   約547行でstatus/write/read/context/human projectionが同居。  
   候補: writer/read model/projectionを内部moduleへ分割。ただしartifact file formatは変更しない。

6. **frontend `web/app.js`分割**  
   約652行。settings/prompt/run polling/turn render/memory renderを分ける。将来prompt管理画面を追加する前に有効。

### 保留

- AgentごとのModelAdapterをすぐ別instance化するrefactorは、研究上のper-Agent model選択仕様とGPU lifecycleを先に決める必要があり、単なる整理としては触らない。
- prompt/output schemaの名前変更やartifact形式変更は再現性・旧run閲覧を壊すので、まず内部コード分割とtest維持を優先。
- `reader/`と`sampling/`の統合は、target_onlyがsequential_loader側のTargetFrameStreamを使い、full_rgbがWorkbench側samplingを使うため、現在は境界として意味がある。単にファイル数削減目的では統合しない。

## 次に比較したいrefactor軸

- 理解しやすさ: 1ファイルの責務数、Agentの入力→出力が追えるか。
- 研究変更耐性: prompt/schema/modelをAgent単位で差し替えやすいか。
- 互換性: 既存run artifact/API/UIを無変更で読めるか。
- test容易性: model callなしでstage/orchestrator/recordを独立検証できるか。
- 差分サイズ: 一回のrefactorで機能変更を混ぜないか。

現時点の第一候補は、**pipeline.pyをAgent実装とorchestratorへ分割 → server.pyをsession/service/HTTPへ分割**の順。prompt CRUD/Agent別modelなどの機能追加は、その後に別specで進める方が安全。

## 2026-09-30 18:11 JST 追記：Agentを「モデル設定」、Workflowを「使い方」に分離する案

ユーザーはオーケストレーションを参考に、研究コードを初見でも説明できる構造へ整理したい。特に現在の`agent/`と`model/`の意味が直感とずれており、**Agent側は「どのモデルをどう使えるか」というモデル/Agent設定に寄せ、Situation/Memory/Answerの呼出し順・入力整形・validation・memory更新などは別の分かりやすい領域へ移す**方向を希望。

### 提案する概念分離

- `agents/` = **誰が考えるか**。model family/backend、model ID、capability、generation、共通Agent wrapperを置く。ファイル名は`qwen3_vl.py`, `fake.py`のようにモデル名中心。
- `workflow/` = **どう仕事をさせるか**。Situation/Memory/Answerの入力作成、出力検証、window→EOFの順序、memory/record連携を置く。
- `VideoQAOrchestrator` = **監督**。1 windowではSituation→Memory、EOFではAnswer、event 0件ではinsufficient_evidence、cancel/record/statusを一つの場所で管理。CLIとserverの双方が同じOrchestratorを呼ぶ。
- `records/` = **何を残すか**、`reader/` = **何を読むか**、`dataset/` = **何を解くか**、という既存境界は基本維持。

候補tree:

```text
src/longvideoqa_workbench/
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── qwen3_vl.py
│   └── fake.py
│
├── workflow/
│   ├── __init__.py
│   ├── video_qa.py          # VideoQAOrchestrator: 全体監督
│   ├── situation.py         # Situationの入力構築・出力schema/validation
│   ├── memory.py            # Memoryの入力構築・event/narrative・budget
│   └── answer.py            # EOF Answer・最終根拠validation
│
├── config/
├── dataset/
├── reader/
├── sampling/
├── records/
├── interfaces/
└── web/
```

prompt assetは当面repository rootの`prompts/en/`を維持。Agentがprompt本文を内包するのでなく、Agent/Workflowの設定が`prompt_id`を参照し、run開始時にresolved prompt/hashを固定する。将来prompt libraryを追加してもAgent/Workflow本体を書き換えずに差し替えられるようにする。

### Agentクラスの役割候補

`Agent`は研究上の役割名そのものではなく、**「model + prompt + generationを用いて1回の推論を行う共通実行単位」**とする。

概念例:

```python
Agent(
    name="situation",
    model=qwen3vl,
    prompt_id="chunk_understanding_video_v1_en",
    generation=GenerationConfig(max_new_tokens=1024),
)
```

入力はWorkflow側で構築した`AgentInput`、出力は生の`AgentResponse`。Situation/Memory/Answer固有のJSON validationはWorkflow側が担当する。こうすると`agents/qwen3_vl.py`はQwenのロード・capability・image/video入力・generateだけに集中し、研究上の役割変更でモデル実装を触らない。

### 現行コードからの主な移動

- `model/qwen3vl.py` → `agents/qwen3_vl.py`
- `model/fake.py` → `agents/fake.py`
- `core/protocols.py`のModelAdapter相当 → `agents/base.py`へ寄せる候補
- `agent/pipeline.py`のSituation/Memory/Answer wrapper + run_window_turn/run_pipeline → `workflow/`
- `agent/observations.py` → `workflow/situation.py`または`workflow/schemas/observation.py`
- `agent/events.py` + 現`agent/memory.py` → `workflow/memory.py`
- `agent/final_output.py` → `workflow/answer.py`
- 旧`agent/`と`model/`は移行後削除候補。ただしimport互換が必要なら一時re-export。

### 「監督」の一本化が重要

現在はCLI側`run_pipeline()`とserver側`TurnSession.advance()`の双方にwindow/EOF進行ロジックがある。リファクタ後は`VideoQAOrchestrator`へ寄せ、外側は次だけを行う:

```text
CLI    ─┐
        ├─> VideoQAOrchestrator.advance()
Server ─┘
             ├─ Situation Agent
             ├─ validate
             ├─ Memory Agent
             ├─ memory/record
             └─ EOFなら Answer Agent
```

この結果、ユーザーが大きな働きを説明するときは以下の4点だけでよい:
1. `agents/`: 利用可能なモデルと1回の生成方法。
2. `workflow/video_qa.py`: 動画QA全体の監督。
3. `workflow/situation.py|memory.py|answer.py`: 各役割の入力と出力契約。
4. `records/`: 実行結果とmemoryの保存。

### リファクタで変えないもの

- Qwenへのvideo_clip方式・sample_fps・`do_sample_frames=False`
- Situation/Memory/Answerのprompt本文・JSON schema
- old image_list runの読取互換
- run artifactのファイル名/JSONL形式
- HTTP API/UIの外部挙動
- `none/previous_text`, insufficient_evidence, EOF Answer
- 同一Qwenを3役割で共有する現在の挙動

Agent別モデル選択やprompt CRUDはこの内部整理の後に追加した方がよい。今回の案はexploratoryで、コード変更/spec化はまだ行わない。

## 2026-09-30 18:29 JST 追記：CrewAI風のAgent/Task/Workflow分離とBrowser・View再編

ユーザー追加意向:
- `dataset/`にはdataset固有adapterだけを残し、search/index/catalog等の外部閲覧機能は別ディレクトリへ。
- `records/`の人間用viewは詳細すぎる可能性。人間向け一次表示は「Situationの区間 [start,end) + window_summary」を時系列に並べ、最後に最終回答だけを示す。観測詳細/event/memory diff/frame根拠/raw prompt等は詳細表示へ。
- `interfaces/`はserver/SQLite/media/translation/browserまで抱え過ぎ。外部I/O境界とBrowser機能・run sessionを分けたい。
- CrewAIの`Agent / Task / Crew / Process`的な運用を参考にし、実依存を導入する必要はない。監督ファイルを一つ、できるだけ短くしたい。

### CrewAIから借りる概念（依存は不要）

CrewAI公式の抽象は、Agent=役割を持つ実行者、Task=具体的な仕事+expected output+担当Agent、Crew=agents/tasksを束ねるチーム、Process=sequential/hierarchicalな実行順。今回のStreaming VideoQAは未来アクセス禁止・再現可能な順序・artifact検証が重要なので、CrewAIそのものを入れて自律delegationさせるより**概念だけ借りた決定的sequential workflow**が適する。

本研究での対応:
- Agent = `model + prompt + generation + role metadata`
- Task = Situation / Memory / Answerの「入力を組み立て、Agentを1回呼び、出力schemaを検証する仕事」
- Crew相当 = VideoQATeam（3 Agent + 3 Task）
- Process相当 = deterministic sequential
- manager LLMは置かず、短いPython `VideoQAOrchestrator` が監督。早押し等を研究するときも、managerの自由判断で未来/追加callを発生させず、明示schemaにする。

ユーザー提示のCrewAI例では`Process.sequential`と`manager_llm`が併記されているが、CrewAI公式ではmanager LLM/manager agentはhierarchical processの調整役。今回の一本道処理には不要。

### 更新した候補tree

```text
src/longvideoqa_workbench/
├── agents/                     # 「何のAIを使うか」
│   ├── base.py                 # Agent / ModelBackend共通契約
│   ├── qwen3_vl.py             # Qwenロード、video/image入力、generate
│   └── fake.py
│
├── workflow/                   # 「Agentに何をさせるか」
│   ├── video_qa.py             # 短いVideoQAOrchestrator（監督）
│   ├── team.py                 # 3 Agent + Taskの組み立て
│   ├── situation.py            # SituationTask + output validation
│   ├── memory.py               # MemoryTask + budget/event validation
│   └── answer.py               # AnswerTask + evidence validation
│
├── datasets/                   # dataset固有の接続だけ
│   ├── longvideobench.py
│   └── fake.py
│
├── browser/                    # datasetを「探す・見る・個人管理する」
│   ├── catalog.py
│   ├── index.py
│   ├── search.py
│   ├── library.py              # favorite/folder/alias SQLite
│   ├── media.py                # thumbnail/preview
│   └── translation.py
│
├── runtime/                    # 実行中sessionとアプリケーション操作
│   ├── session.py              # next/cancel/EOF/reader資源
│   └── run_service.py          # start/restart/get/list
│
├── records/                    # 機械用artifactの保存/読取
│   └── run.py                  # 初回refactorでは形式不変
│
├── views/                      # recordsから決定的に人間用表示を作る
│   └── run_view.py
│
├── interfaces/                 # 最小の外部入口だけ
│   ├── cli.py
│   └── server.py               # HTTP routingのみ。business logicは持たない
│
├── config/
├── reader/
├── sampling/
└── web/
```

名称`interfaces/`自体が分かりづらければ、後続で`entrypoints/`へ改名する候補。初回はimport移動量を抑えるためinterfacesにCLI/HTTPだけ残す案も有力。

### 短い監督ファイル

目標は`workflow/video_qa.py`を「研究の流れが一目で読める」程度にする。例えば概念上:

```python
class VideoQAOrchestrator:
    def process_window(self, context, window):
        observation = self.team.situation_task.run(context, window)
        memory = self.team.memory_task.run(context, observation)
        return context.with_memory(memory)

    def finish(self, context):
        if not context.events:
            return InsufficientEvidence()
        return self.team.answer_task.run(context)
```

実際のstream ownership/cancel/thread/status/thumbnail/HTTPはこのファイルへ入れず`runtime/session.py`へ、JSONLのwriteは`records/`へ委譲する。こうすれば監督は50--100行程度を狙える。短さ自体より「一つの関数で研究フローが読める」ことを優先。

### Agent/Taskの候補API

```python
situation = Agent(
    role="situation",
    model="qwen3_vl",
    model_id="Qwen/Qwen3-VL-4B-Instruct",
    prompt="chunk_understanding_video_v1_en",
    generation={"max_new_tokens": 1024, "temperature": 0.0},
)

situation_task = SituationTask(
    agent=situation,
    expected_output="window_observation_v1",
)
```

Agentはmodel固有backendを選びprompt/generationを保持。Taskは質問/window/memoryをどの変数にするか、画像かvideoか、validationとstructured outputを知る。これで将来Memoryだけ別model、prompt差替えがAgent定義変更だけで済みやすい。

### 人間用view

現状`RunRecord.readable_memory()`がwindows/observations/timeline/versions/diffを一つに構成するため、storageとpresentationが混在。提案:
- `records/`: raw/validated JSON/JSONLと最新snapshotだけ。SSOT。
- `views/run_view.py`: read-only projection。
- 基本view:
  ```text
  00:00–00:04  女性がカメラに向かって話している。
  00:04–00:08  女性が電話を手に取り画面を見る。
  00:08–00:12  電話を机に置く。

  最終回答
  2. She places the phone on the table.
  ```
- 詳細を開くとobservations/unresolved/event importance/evidence frame/actual-target timestamp/memory versions/raw stage/promptへ辿れる。
- 新しいLLM summaryを作らず、既存`window_summary`とfinal answerから決定的に生成。詳細artifact形式は変更しない。

### Browserとdataset/interface

現`dataset/catalog.py,index.py,search.py`はLongVideoBench接続そのものではなくWorkbench browserの閲覧機能。現`interfaces/library.py,media.py,translation.py,browser.py`と一緒に`browser/`へまとめると、`datasets/`は「QuestionSample/catalog sourceを提供するdataset adapter」に集中できる。
`interfaces/server.py`約937行はHTTP、ServerContext、TurnSessionが混在するため、`runtime/session.py`と`runtime/run_service.py`を抽出し、serverはURL→service呼出しの薄いadapterにする。

### 初回リファクタで変えない契約

prompt本文、output JSON schema、video_clip、sample_fps、none/previous_text、EOF Answer、insufficient_evidence、artifactファイル形式、HTTP URL/response、旧run read compatibilityは不変。Agent別model選択やprompt CRUDは構造整理後の機能追加として分離。

現在の方向性は有力だがまだbrainstorm。spec化/コード変更はユーザーの明示依頼後。

## 2026-09-30 18:51 JST 追記：Agent間テキスト状態とPackage Service境界

ユーザーの軌道修正:
- 人間向けテキストはSituation summaryだけではなく、**各windowで実際に動いた全Agentの主要出力**を順番に残したい。現状は各windowでSituation+Memory、EOFでAnswer。
- Agent間で受け渡す主情報も単純なtextに寄せたい。Situationは今見える情報をtext化、Memoryは「前までのmemory text + current situation text + question」を見て、まだ回答に直結しなければmemory textを更新、十分ならAnswerへ渡す構想。
- 詳細なframe/event/timestamp/validation等はmachine artifactとして別保持。
- 各directoryに外部向けの「監督/窓口」を置き、他directoryの内部関数を直接importしない。directory間通信は最小化し、その上に全体監督を置く。

### 現行と将来像の差

現行main `2b5f830`では、Situation/Memoryは各windowで実行、AnswerはEOFのみ。Memory promptはすでに`Previous validated text memory + Current validated observations + Question + frame manifest`を入力し、`events + narrative + unresolved`を返す。ただし「今回答できるか」を判定してAnswerを途中起動する機能はない。これは将来のearly-answer/Decision研究に相当し、リファクタと機能変更を分ける。

### 人間向けAgent trace候補

machine SSOTはJSON/JSONLのまま。そこから決定的に`run_trace.md`（またはAPI view）を生成し、各turnを以下のように表示:

```text
[00:00 - 00:04] Situation Agent
女性がカメラに向かって話している。机上にスマートフォンがある。

[00:00 - 00:04] Memory Agent
まだ質問への決定的な証拠はない。
記憶: 女性はカメラに向かって話しており、机上にスマートフォンがある。

[00:04 - 00:08] Situation Agent
女性がスマートフォンを手に取り画面を見る。

[00:04 - 00:08] Memory Agent
質問に関係する可能性が高い。現在の記憶へ追加する。
記憶: 女性は机上のスマートフォンを手に取り画面を見た。

[END] Answer Agent
2. ...
```

基本traceはrole/区間/主要textだけ。詳細画面/機械recordにprompt ID/hash、raw JSON、observations、events、importance、frame ID、actual/target timestamp、latency、validation errorを残す。別LLMでhuman summaryを再生成しない。

### 将来の単純なAgent間state

研究上のAgent間メッセージはrich JSON全体を毎回渡すのでなく、主に`text`を使い、制御/証跡をsidecar metadataへ分離する案:

```python
SituationResult(
    text="今見えている状況...",
    evidence=...,       # machine-only
)

MemoryResult(
    action="continue",  # 将来: continue | answer
    text="ここまでの記憶...",
    evidence=...,       # machine-only
)
```

Situation Agent: current video window -> situation text。
Memory Agent: question + previous memory text + current situation text -> updated memory text + 将来action。
Answer Agent: question + choices + answer時点のmemory text -> answer。
現在のevent ledger/evidence refsは研究traceabilityのためrecordsへ保持し、Agent間の主contextを複雑にしない。

### directoryごとの「監督」はFacade/Serviceとして設計

ユーザーの直感はpackage boundaryとして有効。ただし全Serviceが横方向に互いを呼ぶと、単に依存がSupervisorへ移って再び複雑になる。そこでルール:
1. 各package内部moduleは原則そのpackageのServiceからだけ外部公開。
2. 他packageは内部file/functionを直接importせず、Serviceまたは明示public contractを呼ぶ。
3. package間で渡す値は`core/contracts.py`等の小さなshared typeだけ。
4. **横方向のService→Service連鎖は最小限**。基本の組み合わせは最上位`VideoQAWorkflow`が行う。
5. browserのような独立機能はVideoQA workflowを知らない。

「監督」という名前を全てSupervisorにせず、人間に役割が伝わる統一語を使用:
- 大監督: `VideoQAWorkflow`（ファイル`workflow/video_qa.py`）
- Agent窓口: `AgentService`
- Dataset窓口: `DatasetService`
- Record窓口: `RecordService`
- Browser窓口: `BrowserService`
- 実行session窓口: `RunService`
- 人間表示窓口: `ViewService`
- 個々の仕事: `SituationTask`, `MemoryTask`, `AnswerTask`

`Manager`や`Supervisor`は役割が曖昧になりやすいため避け、Workflow/Task/Serviceという3語で説明可能にする。

### 依存方向

```text
entrypoints/ (HTTP, CLI)
        |
        v
runtime/ RunService
        |
        v
workflow/ VideoQAWorkflow  <--- 大監督
   |        |        |
   v        v        v
Situation  Memory   Answer Task
        \    |    /
          AgentService
               |
            qwen3_vl

VideoQAWorkflow ---> RecordService
VideoQAWorkflow ---> ViewService (必要時はrecordからprojection)

DatasetService ---> reader/samplingへQuestion/動画情報
BrowserService ---> DatasetService + library/media/translation

禁止例:
workflow/memory.py -> records/run.pyのprivate helper直import
server.py -> agents/qwen3_vl.pyのgenerate直呼び
browser/search.py -> dataset/longvideobench.pyのprivate関数直呼び
```

### 候補treeの更新

```text
src/longvideoqa_workbench/
├── agents/
│   ├── agent.py
│   ├── agent_service.py       # Agent定義/取得の外部窓口
│   ├── qwen3_vl.py
│   └── fake.py
├── workflow/
│   ├── video_qa.py            # VideoQAWorkflow: 短い大監督
│   ├── team.py
│   ├── situation.py           # SituationTask
│   ├── memory.py              # MemoryTask
│   └── answer.py              # AnswerTask
├── datasets/
│   ├── dataset_service.py
│   ├── longvideobench.py
│   └── fake.py
├── browser/
│   ├── browser_service.py
│   ├── catalog.py
│   ├── index.py
│   ├── search.py
│   ├── library.py
│   ├── media.py
│   └── translation.py
├── runtime/
│   ├── run_service.py
│   └── session.py
├── records/
│   ├── record_service.py
│   └── run.py
├── views/
│   ├── view_service.py
│   └── run_trace.py
├── entrypoints/               # 旧interfacesの分かりやすい改名候補
│   ├── cli.py
│   └── server.py
├── core/
├── config/
├── reader/
├── sampling/
└── web/
```

初回リファクタは挙動不変: 現在のEOF-only Answer、prompt/schema/artifact/API、video_clip等を維持。上記future `MemoryResult.action=answer`は後続研究spec。

## 2026-09-30 18:51 JST 追記2：木構造の依存とPresentation層

ユーザーは現在の研究タスクを「datasetから動画を先頭から読み、指定長でsamplingし、Situationが理解、Memoryが整理、Answerが回答、Records/人間向け表示へ残す」という単純な一本道としてコード上にも反映し、将来的な絡まりを避けたい。またviewsがWeb実行へ影響するかを確認。

### 現行Webとの関係

現行main `2b5f830`では`ServerContext.run_payload()`が`record.readable_memory()`を`memory_readable`として返し、`web/app.js`がそれを描画する。したがって現在も「人間用projection」はWebの**表示内容**には影響する。ただしAgent推論/reader/memory更新の実行ロジックには影響しない。リファクタ後もこの一方向性を明示する。

名称は`views/`だとWeb MVCのviewと誤解しやすいため、候補として`presentation/`を推奨。「機械記録から人間向けの見せ方を作る」層。Web用JSONとtext traceを同じrecordから作る。
- `records/`: SSOTのmachine artifactを書き、読む。
- `presentation/`: recordsをread-onlyに読み、Web payload / text traceを決定生成。推論状態を変更しない。
- presentation生成失敗でrun結果をfailedへしない。再生成可能な派生物。

### 研究の一本道をそのまま依存木へ

完全なtreeにはshared contracts/configがあるのでならないが、**main research pathを一方向DAG/木状**にする:

```text
entrypoints/
    |
runtime/ RunService
    |
workflow/ VideoQAWorkflow                  <- 大監督
    |
    +-- DatasetService         何を解くか
    +-- VideoStreamService     先頭から読み、window化
    +-- AgentService           Agent定義を提供
    |     +-- SituationTask
    |     +-- MemoryTask
    |     +-- AnswerTask
    +-- RecordService          機械記録
             |
             v
      PresentationService      人間向け表示（read-only）
             |
       +-----+-----+
       |           |
      Web       text trace
```

重要: DatasetService→VideoStreamService→AgentServiceのようにservice同士が内部で次々呼ぶのではなく、`VideoQAWorkflow`が各窓口を順に呼ぶ。これにより横依存が生えず、「別directoryのprivate関数を知る」必要がない。directory外はpackage rootで公開したService/DTOのみimportする。

### directory監督の形

各directoryには1つの**Service class**を外部窓口として置く。ファイル名は全部`service.py`でもよく、import側ではclass名が意味を説明する:
- `datasets/service.py -> DatasetService`
- `streaming/service.py -> VideoStreamService`
- `agents/service.py -> AgentService`
- `records/service.py -> RecordService`
- `presentation/service.py -> PresentationService`
- `browser/service.py -> BrowserService`
- `runtime/service.py -> RunService`

各package `__init__.py`はServiceと公開DTOだけre-export。例: `from longvideoqa_workbench.datasets import DatasetService`。別packageから`datasets/longvideobench.py::_private`を直接importしない。

大監督だけはServiceではなく、研究フローを表す名前`VideoQAWorkflow`にする。`workflow/video_qa.py`は50-100行程度を目標に、以下だけを読むと処理が説明できる状態:
```python
question = datasets.get_question(...)
with video_stream.open(question, settings) as windows:
    for window in windows:
        situation = situation_task.run(window, question, memory)
        memory = memory_task.run(question, memory, situation)
        records.record_turn(window, situation, memory)

answer = answer_task.run(question, memory)
records.record_answer(answer)
```
実際のcancel/HTTP/thread/cacheはRunService、JSONL serializationはRecordService内部、model具体処理はAgentService内部。

### 人間向けPresentation

基本traceは「ブラウザで確認できるAgentの主要動作」をテキストでも残す:
```text
[00:00-00:04] Situation Agent
<主要出力text>

[00:00-00:04] Memory Agent
<判断text>
Memory: <更新後のmemory text>

...
[END] Answer Agent
<answer>
```

詳細recordには従来のstructured JSON/event/frame/timestamp/prompt/model/latency/validationを保持。基本traceとWebは同じPresentationService projectionを共有し、片方だけ意味が変わらないようにする。

### 将来のAgent flow

現在のMemoryはすでに previous narrative + current validated observations + question を受けるが、AnswerはEOFのみ。将来は:
`Situation video -> situation text`
`Memory(question + previous memory text + situation text) -> updated memory text + continue/answer`
`Answer(question + choices + selected memory text) -> answer`
とする候補。これはearly answerという研究挙動変更なので、今回の構造refactorとは分離したspecにする。

この依存木を守るため、最初のrefactorでは挙動/API/artifact/prompt/schemaを変えず、package移動・Facade抽出・重複orchestration一本化のみを対象にするのが安全。

## 2026-09-30 19:25 JST 追記：Config・Prompt管理・Dataset別ユーザー状態

ユーザーはリファクタspec前の最後の確認として、現configで制御できる範囲、YAMLからprompt選択できるか、prompt CRUD/履歴の実装進捗、prompt directory再編、favorite等のユーザー状態をsrc外・dataset単位で保存する構成を確認したい。

### 現行main `2b5f830` のConfig実態

`config/loader.py`はprofile/recipe/promptをallowlistで解決。

**profile YAML** (`configs/common/longvideobench-qwen3vl.yaml`):
- `dataset_adapter`
- `data_root_name`
- `model_adapter`
- `model_id`
- `generation.max_new_tokens`, `generation.temperature`
- `subtitles_enabled`
- `decoder_frames_per_sample`
- `stages[].name/prompt_id/enabled`

**recipe YAML**:
必須 `profile, question_id, window_seconds, frames_per_window`
任意 `reader_mode, observation_context_mode, visual_input_mode, memory_budget_tokens`

**runtime API**:
recipe項目に加え`prompt_overrides: {stage_name: prompt_text}`を受ける。一回のrunだけの本文上書き。

**video_clip特例**:
profile YAMLの`stages[].prompt_id`は自由選択としては機能せず、`_resolved_stage()`が
- Situation: `chunk_understanding_video_v1_en` / `...with_memory...`
- Memory: `evidence_aggregation_video_v1_en`
- Answer: `final_answer_video_v1_en`
へ強制差替え。image_listでもSituation+previous_textは`chunk_understanding_with_memory_en`へ強制。
従って「どのpromptを使うかをrecipe YAMLから任意に選ぶ」は現状不可。profileにprompt_idはあるがmode resolverが優先する。

video_clipのstage別生成上限もYAMLではなくPython定数`VIDEO_GENERATION_LIMITS`でSituation=1024, Memory=768, Answer=384へ設定。共通temperatureはprofile generationから継承。

Webの新run defaultはserver capabilitiesで`visual_input_mode=video_clip`を明示している一方、CLIのnamed recipeをそのままresolveすると未指定時`image_list`。このdefault差もリファクタ時に明示したい。

### Prompt管理の現行進捗

実装済み:
- repositoryの`prompts/en/*.txt` 8ファイルをallowlist登録。
- mode/contextに応じたbuilt-in presetをserver capabilitiesで返す。
- Webの各stageにprompt本文textareaを表示し、実行前に編集可能。
- 編集本文は`prompt_overrides`としてそのrunへ送る。
- 実runは`resolved_prompts.json`/`execution_settings.json`/`stages.jsonl`へprompt ID/hash/本文をsnapshot保存するため、過去run再現性はある。

未実装:
- 名前・説明付きprompt library
- 保存済みprompt一覧から選択
- 新規作成
- 永続編集/version履歴
- 削除/archive
- Agentごとの「prompt確認」専用画面
- 日本語表示/翻訳cacheと英語sourceの紐付け
- 「最初のプロンプト」/「実装時に作成したプロンプトです」という表示metadata
つまり「textareaでrun単位に一時編集」はあるが、以前合意したCRUD管理はまだ実装されていない。

### Prompt directory再編候補

code repo内のbuilt-in promptと、ユーザー作成promptを分離する。

Repository (read-only built-ins):
```text
prompts/
├── situation/
│   ├── image/
│   │   ├── default_en.txt
│   │   └── with_memory_en.txt
│   └── video/
│       ├── v1_en.txt
│       └── v1_with_memory_en.txt
├── memory/
│   ├── image/default_en.txt
│   └── video/v1_en.txt
└── answer/
    ├── image/default_en.txt
    └── video/v1_en.txt
```

あるいは各promptをfolderにし`prompt.txt + metadata.yaml`とする案:
```text
prompts/situation/video/v1/
├── prompt.en.txt
└── metadata.yaml
```
metadataに`id, role, title, description, language, input_schema, output_schema`を持てるため将来のprompt browserと相性が良い。初期built-inのtitle/descriptionはユーザー指定の「最初のプロンプト」「実装時に作成したプロンプトです」。

User-created promptはrepositoryへ書かず、外部persistent root:
```text
~/.local/share/longvideoqa-workbench/
└── prompts/
    ├── situation/<prompt-id>/
    │   ├── metadata.json
    │   └── versions/0001.txt, 0002.txt, ...
    ├── memory/...
    └── answer/...
```
削除はarchiveを基本とし、run snapshotは不変。PromptServiceがbuilt-in + user libraryを統合してlogical `prompt_id`を解決し、configはpathではなくIDだけ参照する。

### Config再編候補

将来のCrewAI風Agent定義と合わせるなら、prompt selection/model/generationをAgent単位で明示するYAMLが分かりやすい:

```yaml
agents:
  situation:
    model: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: situation.video.initial
    max_new_tokens: 1024
  memory:
    model: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: memory.video.initial
    max_new_tokens: 768
  answer:
    model: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: answer.video.initial
    max_new_tokens: 384

workflow:
  window_seconds: 4
  frames_per_window: 8
  reader_mode: target_only
  visual_input_mode: video_clip
  observation_context_mode: none
  memory_budget_tokens: 6000
```
ただし初回構造refactorでconfig schemaまで変えると挙動変更リスクが上がるため、package移動とは分離して次micro/specで扱う候補。

### Favorite/Folder等の現状と外部保存

現状もsrc/repository内保存ではない。既定は:
`$XDG_DATA_HOME/longvideoqa-workbench/library.sqlite3`
未設定なら
`~/.local/share/longvideoqa-workbench/library.sqlite3`
CLIの`--library-db`で上書き可。

単一SQLiteに`videos(dataset_id, internal_key, alias, favorite, last_used_ns)`、global `folders`、`folder_videos(dataset_id,...)`、translation cacheが共存。データはdataset_idで論理分離されるが、物理ファイルは共通。folder名はglobal。

ユーザー希望のdataset単位物理分離候補:
```text
~/.local/share/longvideoqa-workbench/
├── datasets/
│   ├── longvideobench/
│   │   └── library.sqlite3
│   ├── ego4d/
│   │   └── library.sqlite3
│   └── ...
├── prompts/
│   └── ...
└── app/
    └── settings.json
```
thumbnail/previewはpersistent stateではなく`$XDG_CACHE_HOME/longvideoqa-workbench/...`へ分離維持。

dataset別DBにするとfavorite/alias/recent/folderを完全分離できる反面、「複数datasetをまたぐ1つのfolder」は自然には作れなくなる。現時点のユーザー意向はdataset分離を優先するため、folderもdataset内とする案が有力。translation cacheはdataset状態ではないためglobal cacheへ分離する方が自然。

### Service境界との対応

- `ConfigService`: YAML/Agent設定の解決（将来PromptServiceをlogical IDで利用）
- `PromptService`: built-in + user prompt library、CRUD/version/archive、run用snapshot
- `DatasetService`: dataset adapter
- `BrowserService`: dataset別LibraryStoreを解決
- `UserDataService`またはStoragePaths: XDG persistent root/cache rootのpathのみ統一管理

Prompt CRUDやdataset別DBへのmigrationはユーザーデータを動かすため、単なるpackage refactorとは分け、backup/旧DB import/read-only migration Gateを持つべき。

## 2026-09-30 spec昇格先

ユーザーが段階的に実装へ進むため、以下4本のimplementation spec draftへ昇格した。

1. [Package / Service / Workflow 構造refactor](../../../lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-package-service-workflow-refactor-spec.md)
2. [Agent / Workflow Config 再設計](../../../lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-agent-workflow-config-spec.md)
3. [PromptService / CRUD / Version履歴](../../../lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-prompt-service-crud-spec.md)
4. [Dataset別 User Data / Cache Storage](../../../lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-dataset-user-data-storage-spec.md)

いずれも現時点は`draft`。Stage 1を先に承認・実装し、Stage 2→3→4の順で進める。後段specは先行段階の実装結果を再確認してからapprovedへ上げる。
