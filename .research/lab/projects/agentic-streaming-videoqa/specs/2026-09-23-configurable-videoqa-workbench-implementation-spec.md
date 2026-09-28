---
date: 2026-09-23
project: agentic-streaming-videoqa
status: draft
topic: configurable-videoqa-workbench-implementation
source: 2026-09-18 MTG + 2026-09-23 user-directed configurable adapter / browser prompt design
last_updated: 2026-09-23
---

# Configurable Streaming VideoQA Workbench 実装Spec

## 目的

frame-level text memoryの拡張ではなく、dataset・model・chunk policy・stage promptを組み替えられる、操作可能なStreaming VideoQA実行基盤を作る。

利用者はloopback上のブラウザで登録済みadapterを選び、動画・質問・chunk設定・stageごとのpromptとgeneration parameterを確認または編集して、1 runを開始できる。runは同期的なPython pipelineとして先頭から処理され、設定・実入力・段階ごとの出力を新規artifact directoryへ保存する。画面では実行中/完了/失敗状態と各stageの結果を閲覧・比較できる。

既存の`streaming_text_memory`は本specの実装対象ではない。そこからはQwen3-VLのload / generation経路、`sequential_loader` public API、非上書きartifact、fake model testの考え方だけを参照する。

## Authority / 開始状態

- 現在のユーザー指示: frame-level text memoryとは別の設計とし、model・datasetをadapterで可変にし、chunkと段階別promptをブラウザで確認/変更できるsoftなシステムを設計する。Stepごとにbranch、micro stepごとにcommitする。
- MTG決定: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-18-mtg.md`。
- 関連exploration: `.research/secretary/notes/brainstorm/2026-09-23-minimal-interactive-streaming-videoqa.md`。
- 実装repository: `/mnt/HDD18TB/hayashi/2026_09_hayashi_streaming_video_qa`。
- 調査時branch / HEAD: cleanな`feat/streaming-text-memory` / `1b030974193406fa338eb5bb235a3aeb54c7cf6f`。
- 新実装の開始基準は、実装開始時に上記branch・HEAD・clean worktreeを再確認したものとする。`main`、既存`feat/streaming-text-memory`、既存artifactを変更しない。
- `sequential_loader`はread-onlyのpublic API依存であり、本specの都合で変更しない。
- remoteへのpush、PR作成、merge、mainへのcommit、force push、長時間GPU runは本specの対象外である。

## 採用設計

### 不変kernelと可変recipe

```text
不変kernel
  recipe validation / run lifecycle / sequential execution /
  artifact persistence / error reporting

可変recipe
  dataset adapter / model adapter / chunk policy /
  stage model / generation parameter / prompt template / input binding
```

`videoqa_workbench/`を新規packageとして追加し、既存`streaming_text_memory/`をimport・移動・書換えしない。

初版で利用者に任意のDAG、任意Python、任意shell commandを与えない。登録済みadapterを選ぶ**線形recipe**だけを許可する。これはsoftな比較条件を保存可能にし、stage間の因果順・schemaを検証するためである。

```text
dataset adapter -> ordered frame stream -> chunk policy
    -> chunk-understanding (per chunk)
    -> evidence-update     (per chunk; optional)
    -> final-answer        (EOF後に一度)
```

### Adapter / policy / stageの契約

| 構成要素 | 必須責務 | 初版の実体 |
| --- | --- | --- |
| DatasetAdapter | adapter固有の選択子を検証し、canonicalな`VideoItem`と順序付き`FrameStream`を返す | 既存`sequential_loader` public APIを使う50Salads adapter |
| ModelAdapter | `ModelRequest`（text、画像列、generation設定）を受け、text / raw response / model provenanceを返す。入力capabilityを宣言する | Qwen3-VL Transformers adapter。text-only stageにも同adapterを使える |
| ChunkPolicy | `FrameStream`を先読みせず、timestamp順の`Chunk`へ区切る | fixed-duration policy。時間幅とframe sampling上限をrecipeで指定 |
| Stage | 許可されたinput bindingからpromptを解決し、model呼出し、構造化outputの検証を行う | `chunk-understanding`、任意の`evidence-update`、`final-answer` |

DatasetAdapterはdataset固有の情報を共通streamへ適合するためのAdapterである。chunkingはdatasetの責務に混ぜない。同じdataset / video / modelを固定し、chunk policyだけを比較できるようにする。

初版で本番登録するadapterは50SaladsとQwen3-VLの各1つでよい。ただしfake dataset / fake model adapterをtestに用い、第二adapterを追加してもkernelを変更せず接続できる契約を検証する。別modelやdatasetの実download・実runはこのspecに含めない。

### Recipeと因果性

recipe snapshotには少なくとも以下を含める。

- source: dataset adapter ID、server登録済みdataset rootのID、split、sequence ID。
- question: run開始時に固定する文字列。
- chunk policy: duration、sampling上限、採用frameの規則。
- stages: stage ID、scope（`per_chunk` / `after_eof`）、model adapter ID、generation parameter、prompt template、許可input binding、output schema ID。

`per_chunk` stageはchunk番号順に完了してから次chunkへ進む。`evidence-update`を置く場合、chunk `k`が参照してよいのはchunk `k`の検証済みoutputと`k-1`までのevidenceだけである。`final-answer`はEOF後に一度だけ実行し、final evidenceまたは明示された全chunk outputだけを使う。future chunk、動画全体の事前読み込み、未処理chunk由来のtextを前段stageへ渡してはならない。

`chunk-understanding`はtext memoryを返す必要がない。初版の標準schemaは`observations`、`temporal_events`、`candidate_evidence`、`uncertainty`、`raw_text`とする。schema parseに失敗した場合はraw responseとvalidation errorを保存してrunをfailedにし、後続stageを実行しない。

### Browser UI / server

標準ライブラリHTTP serverとbrowser標準HTML/CSS/JavaScriptだけを使い、既存依存へWeb frameworkを追加しない。hostは`127.0.0.1`を既定とし、外部公開は対象外とする。

UIではstageカードごとに、adapter/model、generation parameter、入力field、prompt template、runtime未確定fieldを明示したpreviewを表示する。利用者はpromptと許可済み設定を編集できる。実行後はそのrunで実際に解決したprompt、input概要、raw response、parse済みoutput、validation error、elapsed timeを読む。

prompt variableは`{{question}}`、`{{chunk.start}}`、`{{chunk.end}}`、`{{chunk.frames}}`、`{{previous.evidence}}`、明示された前stage outputだけを許可する。Run前に未解決variable、scope不整合、画像inputを受けないmodelへの画像binding、schema不整合をHTTP 400で拒否する。ブラウザから任意コード・任意command・adapter upload・既存artifactの編集/削除を許可しない。

dataset rootはserver起動時にIDとpathの対応として登録したものから選ぶ。ブラウザに任意filesystem pathを送らせない。datasetを追加するにはserver側でadapterとroot登録を追加する。

必要な最小endpointは次とする。

| endpoint | 振る舞い |
| --- | --- |
| `GET /` | workbenchのsingle-page UIを返す |
| `GET /api/capabilities` | 登録済みadapter、dataset root、model capability、許可設定を返す |
| `POST /api/recipe/preview` | recipeを検証し、resolved可能部分と未確定runtime fieldを返す。modelは実行しない |
| `POST /api/runs` | 検証済みrecipe snapshotを新規run directoryへ保存し、単一の同期的worker processを開始してrun IDを返す |
| `GET /api/runs` / `GET /api/runs/<id>` | run statusと保存済みstage outputを返す |

UIのpollingはrun状態を読むためだけに使う。worker内部のstage実行は同期的・逐次的で、複数サーバ間通信、queue、node graph、live token streamingは導入しない。

### Artifact / provenance

runごとに新しい`outputs/<run-id>/`を`exist_ok=False`で作り、既存runを上書き・resumeしない。少なくとも次を保存する。

- `recipe_snapshot.json`: UI編集後のrecipe全文、prompt本文、adapter / policy ID、generation parameter、code revision。
- `run_status.json`: queued / running / succeeded / failed、stage、開始/終了、失敗理由。
- `chunks.jsonl`: chunk ID、時刻範囲、実際に採用したframe index / timestamp、chunk provenance、stage出力への参照。
- `stages.jsonl`: stage ID、chunk IDまたはEOF、resolved prompt、input summary、raw response、validated output、error、elapsed time、model provenance。
- `final_answer.json`: final answer、参照したevidence / chunk ID、入力hash。

dataset画像、model weight、credential、絶対pathはartifactやUIの既定表示へ保存しない。dataset root ID、相対選択子、model ID/revision、recipe hash、Git revisionは保存する。画像をartifactへcopyしない。

## 変更範囲と互換性

- 新規: `videoqa_workbench/`、`scripts/run_videoqa_recipe.py`、`scripts/serve_videoqa_workbench.py`、tests、READMEの利用説明。
- 既存`streaming_text_memory/`、既存CLI、`scripts/smoke_sequential_loader.py`、既存outputsの外部挙動を変更しない。
- `sequential_loader`は`import sequential_loader as sl`のpublic APIだけを使う。
- 新UIは既存EgoCross trace viewerと別のapplicationであり、EgoCross repoやread-only viewerを変更しない。

## Branch・commit運用

実装開始時に基準branch / HEAD / worktreeのclean状態を確認する。**1 Step = 1 branch**、**1 micro step = 1 commit**とし、micro stepでbranchは増やさない。Step末尾testが成功した直前Step HEADからのみ次branchを切る。失敗時は同一branchに`fix:`または`test:` commitを追加し、成功まで次branchを作らない。

commit titleは以下の表の文言を使う。本文には`対象:`、`変更:`、`理由:`、`検証:`、`影響:`、`次:`を日本語で各一行ずつ含める。各commit前に対象diffと対応testを確認する。outputs、dataset画像、model weight、credentialをcommitしない。local commitは本spec承認後に許可されるが、push / PR / mergeは別途明示指示が必要である。

```text
feat/streaming-text-memory @ 1b03097 (clean; 実装開始時に再確認)
└── feat/step-01-workbench-contract
    └── feat/step-02-workbench-adapters
        └── feat/step-03-workbench-recipe-runner
            └── feat/step-04-workbench-artifacts
                └── feat/step-05-workbench-server
                    └── feat/step-06-workbench-console
                        └── feat/step-07-workbench-verification
```

### Step 01: configuration and contract

**Branch:** `feat/step-01-workbench-contract`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 01.1 | `feat: add workbench recipe schema` | immutable recipe、stage scope、allowed binding、canonical input/output dataclassを追加する |
| 01.2 | `test: validate workbench recipe contracts` | missing variable、unknown adapter、scope / capability / schema不整合をfake registryで拒否する |
| 01.3 | `docs: describe workbench recipe contract` | recipeの可変部分、不変kernel、非対応のDAG / arbitrary codeをREADMEへ記載する |

**Step末尾test:** `python3 -m unittest discover -s tests -p 'test_*.py'`、`python3 -m py_compile videoqa_workbench/*.py scripts/*.py`。

### Step 02: adapters and ordered chunk source

**Branch:** `feat/step-02-workbench-adapters`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 02.1 | `feat: add dataset and model adapter protocols` | capabilityを持つregistry、fake dataset / model adapterを追加する |
| 02.2 | `feat: add 50salads workbench adapter` | public `sequential_loader` APIだけで選択子からordered frame streamを返す |
| 02.3 | `feat: add fixed-duration chunk policy` | streamを先読みせず、時刻範囲・採用frame provenance付きchunkへ変換する |
| 02.4 | `feat: add Qwen3-VL workbench adapter` | workbench契約でQwen3-VL text/image generationを行い、model provenanceを返す |
| 02.5 | `test: cover adapter and chunk boundaries` | fake adapterで順序・non-preload・sampling上限を検証し、50Salads public API利用をtestする |

**Step末尾test:** Step 01 test、adapter / chunk unit test、`python3 -m py_compile videoqa_workbench/*.py scripts/*.py`。実model load、dataset runはしない。

### Step 03: linear recipe runner

**Branch:** `feat/step-03-workbench-recipe-runner`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 03.1 | `feat: resolve stage prompt bindings` | allowlist variableだけを解決し、runtime未確定fieldを明示できる |
| 03.2 | `feat: run per-chunk understanding stages` | chunk順にmodel adapterを呼び、構造化outputとraw textを得る |
| 03.3 | `feat: run causal evidence update stages` | optional evidence stageがcurrent chunk outputと過去evidenceだけを使う |
| 03.4 | `feat: run EOF final answer stage` | EOF後に一回だけfinal stageを実行し、future入力を使わない |
| 03.5 | `test: cover linear recipe causality` | fake modelでcall順、binding、停止、final一回、future遮断を検証する |

**Step末尾test:** 全unit test、compile、fake adapterによる2-chunk end-to-end smoke。

### Step 04: immutable run artifacts and CLI

**Branch:** `feat/step-04-workbench-artifacts`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 04.1 | `feat: persist recipe snapshots and run status` | 新規run directory、recipe snapshot、status遷移、non-overwriteを実装する |
| 04.2 | `feat: persist chunk and stage provenance` | chunks / stages JSONL、raw response、validated output、failure contextを逐次保存する |
| 04.3 | `feat: add videoqa recipe runner CLI` | recipe fileを受けて同期workerを実行するCLIを追加する |
| 04.4 | `test: cover workbench artifacts and CLI` | snapshot不変性、既存run非変更、途中失敗、CLI validationをtestする |

**Step末尾test:** 全unit test、compile、`python3 scripts/run_videoqa_recipe.py --help`、fake adapterを使うartifact smoke。

### Step 05: loopback workbench API

**Branch:** `feat/step-05-workbench-server`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 05.1 | `feat: expose workbench capabilities and preview API` | capability一覧と非実行previewを提供し、不正recipeをHTTP 400にする |
| 05.2 | `feat: start and report workbench runs` | 新規snapshotを作り単一workerを開始し、status / outputをread-only APIで返す |
| 05.3 | `test: cover workbench API boundaries` | loopback限定、run ID検証、未登録root / adapter、path traversal、不正recipeをtestする |

**Step末尾test:** 全unit test、`python3 scripts/serve_videoqa_workbench.py --help`、synthetic fixtureのloopback API smoke。GPU inferenceはしない。

### Step 06: browser recipe console

**Branch:** `feat/step-06-workbench-console`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 06.1 | `feat: add workbench console static shell` | 外部frontend dependencyなしのHTML / CSS / JavaScript shellを追加する |
| 06.2 | `feat: edit and preview workbench recipes` | source、chunk、stage card、prompt、generation設定、validation結果を表示・編集できる |
| 06.3 | `feat: render workbench run status and outputs` | run開始、polling、stage output、raw response、parse error、provenanceを表示する |
| 06.4 | `test: cover workbench console rendering` | prompt由来文字列のtext表示、validation error、run失敗、runtime placeholderをtestする |

**Step末尾test:** 全unit test、compile、synthetic recipeを使うbrowser手動確認。実Qwenは実行しない。

### Step 07: integration verification and documentation

**Branch:** `feat/step-07-workbench-verification`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 07.1 | `test: cover workbench end-to-end fake run` | UI APIからfake 2-chunk runを開始し、snapshot、順序付きstage output、final answer、失敗表示まで検証する |
| 07.2 | `docs: document configurable workbench usage` | server起動、adapter / root登録、recipe編集、比較時の固定条件、保存artifact、対象外をREADMEへ記載する |

**Step末尾test:** 全unit test、全scriptの`--help`、compile、fake adapterのloopback end-to-end smoke。

## 成功条件

### 実装成功

1. model / dataset / chunk / prompt / generation parameterをrecipe snapshotとして保存し、完了runを後から変更しない。
2. fake adapterを用いて、少なくとも二つのchunkを入力順に処理し、future chunkをper-chunk stageへ渡さない。
3. browserで登録済みadapter・rootを選び、chunk設定とstage別promptをpreview / 編集してrunを開始できる。
4. UIとartifactの双方で、resolved prompt、入力provenance、raw response、validated output、error、model provenanceを確認できる。
5. invalid variable / capability / schema / root / run IDを実行前またはAPI境界で拒否する。
6. 既存Streaming Text Memory CLIとloader smokeが非回帰である。
7. Step branch・micro-step commit規約を守り、各Step末尾testが成功した後だけ次branchを作る。

### このspecで評価しないこと

- VideoQA accuracy、dataset横断の一般化、promptの優劣、long-videoの性能主張。
- 実Qwenのdownload / GPU inference、full video / benchmark / training。
- 任意DAG / node editor、distributed agent、live token streaming、resume、外部ネットワーク公開。
- 第二の実dataset / 実model adapterの導入。contract確認用fake adapterは含む。

## Approval Gate / Implementation Handoff

このspecは`draft`である。保存だけが許可されており、branch作成、コード変更、local commit、server起動、実model load、GPU runは許可しない。実装開始には、次を明示承認する。

1. 新package `videoqa_workbench`を追加し、既存`streaming_text_memory`を変更対象外とすること。
2. 初版を登録済みadapterによる線形recipe、loopback UI、同期workerに限定すること。
3. 上記のStep branch / micro-step commit本文6行規約で実装すること。

- approved spec: 本文書（現時点ではdraft）
- 実装目的: adapterとrecipeにより可変なStreaming VideoQAを、ブラウザから設定・実行・比較できるようにする。
- 基準repository/commit: `feat/streaming-text-memory` / `1b03097`。実装開始時に再確認する。
- 変更scope: 新規workbench package、CLI、loopback server、static UI、test、README。
- 対象外・維持条件: 既存text-memory package / CLI、`sequential_loader`、既存artifact、main、remote push、GPU runを変更しない。
- success criteria: 各Step末尾test、fake adapterでの2-chunk end-to-end、browserでのrecipe編集・preview・run閲覧。
- 許可されている短時間検証: 承認後のunit / compile / CLI help / fake adapter / loopback smoke。
- 長時間runの許可状態: 未許可。実Qwen / GPU / 実dataset runは別途明示指示を必要とする。
- 未検証予定: 実モデル対応、実データ接続、VideoQA精度、モデル/データセット比較。
