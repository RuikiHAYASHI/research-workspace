---
date: 2026-09-18
project: agentic-streaming-videoqa
status: draft
topic: egocross-agent-viewer-launch
source: 2026-09-18 user request + existing 2026-09-18 EgoCross trace viewer specs + current implementation investigation
last_updated: 2026-09-18
---

# EgoCross Agent実行からtrace viewer起動までを単一CLIへまとめる計画

## 目的

現状は、`scripts/observe_egocross.py --agent` がQwen3-VLをloadしてAgent traceを保存し、別途`python3 scripts/serve_trace_viewer.py`が既存traceをブラウザへ表示する二段階である。

この計画では、`scripts/serve_trace_viewer.py`に明示的なAgent実行オプションを追加する。利用者は一つのcommandから、**選択した複数recordのAgent trace生成、loopback viewerの起動、同一browserでの閲覧**まで行えるようにする。Qwen推論はserver起動前に完了させ、viewerは保存済みartifactを読む既存設計を維持する。

```bash
CUDA_VISIBLE_DEVICES=2,3 .venv/bin/python scripts/serve_trace_viewer.py \
  --agent --record-id 712 --record-id 478 --record-id 823 \
  --max-new-tokens 256 \
  --output-root outputs/2026-09-18-action-trace \
  --host 127.0.0.1 --port 8000
```

このcommandは各recordの新規runを同じ`output-root/<run-id>/`へ保存した後に、`http://127.0.0.1:<port>/`を標準出力へ表示する。Edge等のブラウザ起動は利用者が行う。viewerのselectorでは、三recordの全frameを一つのbrowser tabから切り替える。

## 現在の構成と根拠

- `scripts/observe_egocross.py`は`--observe`または`--agent`指定時にだけ`Qwen3VLObserver`を生成する。`--agent`では、一つのmodel / processor instanceをrun中再利用し、各frameで現在画像一枚の観測と画像なしのstate更新を順に行う。
- `egocross_observation/qwen.py`は`Qwen3VLForConditionalGeneration.from_pretrained(...)`と`AutoProcessor.from_pretrained(...)`により、既定`Qwen/Qwen3-VL-4B-Instruct`をloadする。生成は`do_sample=False`である。
- `scripts/serve_trace_viewer.py`と`egocross_observation/viewer.py`は既存の`frames.jsonl`、`run_metadata.json`、dataset画像をread-onlyで提供する。Qwen、PyTorch、GPUは使用しない。
- `2026-09-18-egocross-action-trace-viewer-refactor-spec.md`はID 712、478、823を同じoutput rootで閲覧する契約を定める。一方、従来のviewer spec群ではQwen実行を対象外としている。

上記の承認済みaction-trace specに従い、本計画で選択可能なrecord IDを次の三つへ固定する。

| 表示順 | record ID | dataset | question type | 全frame数 |
| ---: | ---: | --- | --- | ---: |
| 1 | 712 | ExtrameSportFPV | special action identification | 5 |
| 2 | 478 | ENIGMA | action temporal localization | 8 |
| 3 | 823 | ExtrameSportFPV | action sequence identification | 8 |

三recordを選んだ完全runは合計21 frameである。実行時の指定順に関係なく、run・viewer selectorの順序はこの表の712 → 478 → 823に正規化する。

本変更は後者を破棄せず、**`--agent`なしでは従来どおりQwenをloadしないread-only viewer**、`--agent`時だけrunを先行実行する互換拡張とする。

## 採用する実行契約

### CLI

`serve_trace_viewer.py`へ以下を追加する。

| 引数 | 契約 |
| --- | --- |
| `--agent` | Agent traceを生成してからviewerを起動するopt-in flag。未指定時は現在のread-only viewer。 |
| `--record-id ID` | `--agent`時に一つ以上必須。繰り返し指定して、上表のID 712 / 478 / 823から一つ以上を選択する（例: `--record-id 712 --record-id 478 --record-id 823`）。重複IDおよび上表以外のIDはmodel load前に拒否する。 |
| `--max-frames N` | 任意。指定時だけ先頭N frameに制限する。正の整数でなければ拒否する。 |
| `--manifest PATH` / `--dataset-root PATH` | Agent runとviewerが同じ入力を使うための既存既定値を持つpath指定。 |
| `--model-id` / `--model-revision` / `--dtype` / `--device-map` / `--max-new-tokens` | 既存`observe_egocross.py`と同じ既定値・意味でQwen runtimeを指定する。 |
| `--output-root` / `--host` / `--port` | 既存viewerの契約を維持する。hostは`127.0.0.1`のみ許可する。 |

`--agent`なのに`--record-id`がない場合は、modelをloadする前に明示的なargument errorで終了する。`--agent`なしに`--record-id`やmodel設定を渡した場合も入力誤りとして拒否する。

### 起動順

```text
CLI引数・dataset・manifestを検証
  → 選択した全recordの質問種別・frame数・全画像参照を検証し、712 → 478 → 823へ正規化
  → Qwen model / processorを一度だけload（--agent時のみ）
  → 各recordごとに新規run IDを作成し、因果順にAgent処理してJSONL・metadataをflush保存
  → TraceViewerを構成
  → 127.0.0.1のHTTP serverを起動
  → 利用者が表示されたURLをブラウザで開く
```

同じmodel / processor instanceを全選択recordで再利用し、recordごと・frameごとに再loadしない。いずれかのrecordの途中frameで失敗した場合、既存`observe_egocross.py`と同じく保存済みのframe行とerrorは残すが、後続recordを実行せずHTTP serverも起動しない。runの成否が曖昧なままviewerを提供しないためである。

### 保持する因果性・再現性

- 観測入力は質問・選択肢・現在画像一枚だけ、policy入力はprevious text stateとcurrent observationだけとする。過去画像、future frame、final answerを入力へ加えない。
- CUDA device選択は`CUDA_VISIBLE_DEVICES`をshellで与える。source code、run metadata、configへ物理GPU番号を保存しない。
- model ID、取得できたcheckpoint revision、generation parameters、manifest hash、code revisionは既存の`run_metadata.json`契約で保存する。
- recordごとに新run IDを用い、全runを同じ指定`output-root`へ保存する。既存`outputs/`、dataset、manifest、traceを上書き・移行しない。

## 実装方針

### 1. CLIから独立したAgent run関数を作る

現在`observe_egocross.py`の`main()`にある入力検証、record / reference解決、run ID生成、`Qwen3VLObserver`生成、metadata保存、`write_agent_trace()`呼出しを、package側の小さな実行関数へ切り出す。共有関数は一recordを実行する既存経路を保ち、viewer用のorchestrationは選択record列を検証・正規化した後に、一つのobserverを渡して順に呼び出す。

`observe_egocross.py`と`serve_trace_viewer.py`はこの関数を呼ぶ。viewer scriptから別Python processをsubprocessで起動しない。これにより引数・metadata・例外・trace保存の契約を二重実装しない。

既存のdecode-onlyと`--observe`経路は振る舞いを変えず、共有化による非回帰testを置く。

### 2. viewerの既定read-only性を保つ

`serve_trace_viewer.py`が`--agent`を受けない既存commandは、`qwen.py`の重い依存関係やcheckpointに触れず、保存済みrunのHTTP配信だけを行う。viewer backendの`TraceViewer`とHTTP endpointは、Agent実行の責務を持たない。

`--agent`時だけscriptのcomposition rootで複数record用Agent orchestrationを呼び、全recordの成功後に現在と同じ`TraceViewer` / `serve_trace_viewer()`を一回だけ起動する。

### 3. 文書と利用例を更新する

READMEとAgent実行手順に、次を明記する。

- read-only viewer起動と、Agent run付きviewer起動の違い
- Agent runにはVLM依存、checkpoint、GPUが必要であること
- Qwenのloadはブラウザアクセスではなくserver起動前の一回だけであること
- 複数recordのrunを同じoutput rootへ保存し、ID 712 → 478 → 823の順で一つのselectorから読めること
- `CUDA_VISIBLE_DEVICES=2,3`は必要な実行環境でshellから与えること

## 変更予定範囲

| パス | 変更 |
| --- | --- |
| `egocross_observation/` の新規または既存runtime module | `observe_egocross.py`から切り出す共有Agent run orchestration。 |
| `scripts/observe_egocross.py` | 既存CLIを共有orchestrationへ接続し、既存動作を維持する。 |
| `scripts/serve_trace_viewer.py` | 反復可能な`--record-id`、`--agent`とAgent runのCLI引数を追加し、選択recordの全成功後にviewerを一回だけ起動する。 |
| `tests/` | shared run、複数record順序・失敗停止、viewer CLIの分岐、既存CLI非回帰をfake observerで検証する。 |
| `README.md`、Agent実行手順 | 単一command workflowと依存・安全境界を説明する。 |

`egocross_observation/viewer.py`のHTTP API、static UI、trace schema、prompt、Reducer、model adapterの推論契約は変更しない。

## Step / branch / commit計画

### 開始基準と共通規約

- 実装repositoryは`/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation`とする。
- 調査時点の基準はcleanな`feat/step-13-action-trace-viewer-verification`、HEAD `101f5ed`である。実装開始時にもbranch、HEAD、worktreeがcleanであることを再確認する。
- `main`、既存branch、既存trace、dataset、model cacheを変更しない。push、PR、mergeは本planの対象外とする。
- **1 Step = 1 branch**とする。各Step末尾の必須testが成功してから、直前StepのHEADを基に次branchを作る。
- **1 micro-step = 1 commit**とする。複数micro-stepを同じcommitに混在させない。commit titleは下表の文言を使う。
- 各commit本文には、`対象`、`変更`、`理由`、`検証`、`影響`、`次`を日本語で各一行ずつ記載する。
- micro-stepごとに対象diffと対応testを確認する。Step末尾testが失敗した場合は同じbranchで`fix:`または`test:` commitを追加し、成功するまで次branchを作らない。
- `outputs/`、dataset画像、model weight、credentialをcommitしない。GPU inference、dataset更新、既存artifactの書換えはcommit工程に含めない。

```text
feat/step-13-action-trace-viewer-verification  （基準 101f5ed）
└── feat/step-14-agent-viewer-runner
    └── feat/step-15-multi-record-agent-viewer
```

### Step 14: shared Agent trace runner

**Branch:** `feat/step-14-agent-viewer-runner`

**目的:** 既存`observe_egocross.py --agent`の一record実行を、viewerからも安全に再利用できるpackage側のorchestrationへ切り出す。decode-only / `--observe` / `--agent`の既存CLI契約を維持する。

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 14.1 | `refactor: extract reusable agent trace runner` | 一recordの入力検証後に、既存のrun ID作成、metadata保存、`write_agent_trace()`を実行する共有関数を追加する。新規model loadやrecord選択の責務をviewer backendへ入れない。 |
| 14.2 | `refactor: route agent CLI through trace runner` | `observe_egocross.py --agent`を共有関数へ接続する。`--observe`とdecode-onlyの出力、入力検証、run artifact形式を変更しない。 |
| 14.3 | `test: cover reusable agent trace runner` | fake observerで、一recordのJSONL / metadata、state連続性、例外時flush、既存CLIのAgent経路を検証する。 |

**Step末尾test:** `.venv/bin/python -m pytest -q`、`python3 -m compileall egocross_observation scripts`、`.venv/bin/python scripts/observe_egocross.py --help`。

**次branch:** test成功後に`git switch -c feat/step-15-multi-record-agent-viewer`。

### Step 15: multi-record Agent viewer launch

**Branch:** `feat/step-15-multi-record-agent-viewer`

**目的:** `serve_trace_viewer.py --agent`でID 712 / 478 / 823を複数選択し、modelを一度だけloadして順にtraceを作成した後、同一output rootを一つのloopback viewerで開けるようにする。

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 15.1 | `feat: accept multiple action trace records` | 反復可能な`--record-id`を追加し、712 / 478 / 823だけを一つ以上受理する。重複・対象外ID・`--agent`なしのrun用引数をmodel load前に拒否し、実行順を712 → 478 → 823へ正規化する。 |
| 15.2 | `feat: launch selected agent traces before viewer` | 選択recordの参照を全て検証してからobserverを一度だけ生成する。各recordを同じoutput rootの別runとして順に保存し、全成功後にserverを一度だけ起動する。失敗時は後続recordとserver起動を止める。 |
| 15.3 | `test: cover multi-record agent viewer flow` | fake observerで単一load、三runの保存順、同一viewerのrun selector、画像endpoint、途中failure時の停止、read-only起動時のモデル非loadを検証する。 |
| 15.4 | `docs: document multi-record agent viewer launch` | READMEとAgent実行手順へ、反復`--record-id`、同一browserでの切替、GPU環境変数、Qwenのload時点、artifact非破壊を記載する。 |

**Step末尾test:** `.venv/bin/python -m pytest -q`、`python3 -m compileall egocross_observation scripts`、`.venv/bin/python scripts/observe_egocross.py --help`、`python3 scripts/serve_trace_viewer.py --help`、synthetic fixtureによるloopback API smoke。

**完了条件:** fake observerを使うtestで、712・478・823のrunが同じoutput rootに生成され、viewer APIが全三runを固定順で返す。browser / GPUを用いるsmokeは、下記の別途許可後にのみ実行する。


## 検証計画

### 自動検証（モデルdownload・GPUなし）

- shared Agent run関数がfake observerでmetadataとframe JSONLを作成する。
- `observe_egocross.py --agent`が従来と同じ引数・出力契約を維持する。
- `serve_trace_viewer.py --agent --record-id 712 --record-id 478 --record-id 823`が、Qwen observerを一度だけ構成し、712 → 478 → 823の三runを同じoutput rootへ保存した後、viewerを一回だけ構成する。
- `--agent`なしのviewer起動ではobserver生成・Transformers import・checkpoint loadがない。
- `--agent`と`--record-id`の不正な組合せ、重複または対象外のrecord ID、dataset / manifest / frame数 / token数の不正値をmodel load前に拒否する。
- 生成済み三runが既存viewer APIと画像endpointから閲覧可能で、selectorの優先順が712 → 478 → 823である。
- 478のような途中recordが失敗した場合、後続823を実行せず、HTTP serverを起動しない。
- `pytest`一式、`python3 -m compileall egocross_observation scripts`、両CLIの`--help`を実行する。

### 手動短時間smoke（別途実行許可が必要）

GPU利用が許可された場合にのみ、各recordを1 frameに限定して以下を実行する。

```bash
CUDA_VISIBLE_DEVICES=2,3 .venv/bin/python scripts/serve_trace_viewer.py \
  --agent --record-id 712 --record-id 478 --record-id 823 \
  --max-frames 1 --max-new-tokens 256 \
  --output-root outputs/2026-09-18-agent-viewer-smoke \
  --host 127.0.0.1 --port 8000
```

保存された三runを`http://127.0.0.1:8000/`で開き、selectorから712、478、823を切り替え、それぞれで画像、observation、Agent decision、state diff、model metadataが表示されることを確認する。GPU run、モデルdownload、ブラウザ起動はこのplanの保存だけでは許可されない。

## 対象外

- ブラウザのHTTP requestを起点にQwenを推論するlive inference、逐次tail、WebSocket、実行中progress表示、停止・再実行ボタン。
- viewerからのrun削除、artifact編集、dataset / manifest更新。
- final QA、選択肢採点、accuracy、全件評価、run比較。
- 外部ネットワーク公開、hostの`127.0.0.1`以外へのbind、認証、クラウド配信。
- model、prompt、Reducer、Agent state schema、因果入力境界の研究上の変更。

## Blocking / Non-blocking

### Blocking

なし。record選定、複数指定、実行順、失敗時停止、および同一browserでの閲覧は、本計画と参照specで確定している。

### Non-blocking

- shared orchestration moduleの正確なファイル名は、既存packageの命名に合わせて実装時に決める。
- run終了後に標準出力へ表示するrun directory・URLの文言は、既存CLIのstyleに合わせる。
- port競合時は既存どおり`--port`で利用者が変更する。

## Approval Gate

この文書は`draft`であり、コード変更、branch作成、commit、Qwen download / load、GPU実行、server起動を許可しない。実装開始には、本文の複数record契約と対象外を明示承認する必要がある。

## Implementation Handoff

- approved spec: 本文書（現時点ではdraft）
- 実装目的: `serve_trace_viewer.py --agent`から、ID 712 / 478 / 823のうち明示選択した一つ以上のAgent traceを同じoutput rootへ生成後、一つのloopback viewerを起動する。
- 基準repository/commit: `/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation`、`feat/step-13-action-trace-viewer-verification`、`101f5ed`（調査時clean）。
- 変更scope: shared Agent run orchestration、二つのCLI、test、利用文書。
- 対象外・維持条件: viewerの既定read-only性、loopback限定、既存traceの非破壊、current-image-only / previous-text-state-only入力境界を維持する。
- success criteria: 自動検証項目を満たし、別途許可された各1 frame GPU smokeで、三runを同一browserから切り替えて確認できる。
- 許可されている短時間検証: 実装承認後のpytest、compileall、CLI help、fake observerによるloopback smoke。
- 長時間runの許可状態: 未許可。Qwen load・GPU runも別途明示許可が必要。
- 未検証予定: 実モデルの品質、最終QA正答、全21 frameのGPU実行。

## 関連記録

- `specs/2026-09-18-egocross-action-trace-viewer-refactor-spec.md`
- `specs/2026-09-18-egocross-trace-viewer-delivery-plan-spec.md`
- `specs/2026-09-18-egocross-demo-agent-run-spec.md`
- `.research/secretary/notes/brainstorm/2026-09-18-egocross-agent-trace-readability.md`

## 追記: AgentState JSONのviewer表示

### 目的

選択中のAgent trace frameについて、Agent判断の入力になった`state_before`と、Reducer適用後に次frameへ渡る`state_after`を、利用者が整形JSONで確認できるようにする。これは因果的なtext-stateの可視化であり、推論・state再計算・artifact書換えは行わない。

### 表示契約

- `mode: agent`のframeで、既存JSONLの`agent.state_before`を「Agent判断前の入力state」、`agent.state_after`を「Reducer適用後に次frameへ引き継ぐstate」として、別々に整形JSONで表示する。
- 値はtraceに保存済みのJSONをそのまま表示する。過去画像、過去observation、過去の生`AgentDecision` JSONをviewer側で再構成したり、Agent判断の入力へ追加したりしない。
- `scene_summary`、`event_ledger`、`watch_next`、`uncertainties`の全fieldを省略しない。表示例は以下とする。

```json
{
  "scene_summary": [],
  "event_ledger": [
    {
      "event_id": "cup_pickup",
      "claim": "人物が赤いカップを持ち上げ始めた",
      "first_frame": 1,
      "last_evidence_frame": 1,
      "evidence": "手がカップに触れている"
    }
  ],
  "watch_next": [
    {
      "event_id": "cup_pickup",
      "question": "カップが机から離れるか確認する"
    }
  ],
  "uncertainties": []
}
```

- frame切替時には、そのframeの`state_before` / `state_after`へ更新する。`KEEP`はstateを変更しないため、両JSONが同一になる。
- Agent traceではないrun、または当該fieldのない旧traceでは、値を推測せず「AgentStateは利用不可」と表示する。既存の画像、observation、Agent decision、state diff、metadata表示を壊さない。

### 互換性・対象外

- HTTP APIと`frames.jsonl` / `run_metadata.json`のschemaは変更しない。既存frame payloadの`agent` fieldを用いる。
- model、prompt、Reducer、AgentState schema、因果入力境界は変更しない。`KEEP`を新たな履歴として保存する変更も対象外とする。
- 本追記により、本文中の「static UIを変更しない」という範囲は、AgentState JSONを表示する最小のUI変更に限って置き換える。HTTP APIの契約は維持する。

### Step 16: AgentState JSON viewer

**Branch:** `feat/step-16-agent-state-json-viewer`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 16.1 | `feat: display agent state JSON in viewer` | 選択frameの`state_before` / `state_after`を整形JSONで表示し、Agent外run・欠損fieldでは利用不可を表示する。推論、trace schema、HTTP APIは変更しない。 |
| 16.2 | `test: cover agent state JSON viewer display` | agent runのstate前後、`KEEP`時の同一state、Agent外run・欠損stateの表示を既存viewer test styleで検証する。 |

**Step末尾test:** `python3 -m pytest -q`、`python3 -m compileall egocross_observation scripts`、synthetic Agent traceによるloopback viewer smoke。

### 追加の成功条件

- Agent traceの任意frameを選ぶと、保存済み`state_before`と`state_after`がJSONとして読み取れる。
- 表示のみであり、モデルロード、GPU利用、traceの変更、過去frame情報の新規入力は発生しない。
