---
date: 2026-09-16
project: agentic-streaming-videoqa
status: implemented
topic: egocross-agent-text-state-implementation
source: 2026-09-16-egocross-observation-prototype-plan-spec.md + 2026-09-16-agent-text-state-design.md + 2026-09-16-continuity-agent-text-state-correction.md
repository: /mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation
baseline_branch: feat/step-04-qwen-observation
baseline_commit: 37babe1
last_updated: 2026-09-16
implementation_branch: feat/step-07-agent-reproducibility
implementation_head: 0288519
---

# EgoCross Agent Text State 実装計画

## 目的

基礎実装のcurrent-frame observationを維持したまま、過去画像を使わないtext-state Agentを追加する。Agentは各frameの観測文と前時刻のtext stateから、状態更新actionを選び、場面・進行中イベント・次に確認する事項を因果順に追跡する。

初期ゴールは、Agentの状態遷移とtraceを実Qwen3-VLで短いEgoCross画像列に対して動作確認することである。最終QA、正解率、957件全体実行、Agent品質の研究的結論はこの計画に含めない。

## 現在の基準と実行環境

- 基準repository/branch/commit: `2026_09_hayashi_egocross_observation`の`feat/step-04-qwen-observation`、`37babe1`。
- 基礎実装は、manifest読込、JSON順の逐次decode、JSONL trace、current-image-only Qwen adapterを持つ。
- 専用`.venv`にはPython 3.12.3、PyTorch 2.14.0+cu130、Transformers 5.17.0、Accelerate 1.15.0、Pillow 12.3.0が導入済みである。
- `Qwen3VLForConditionalGeneration`のimportとCUDA 4 deviceの検出は確認済みである。
- default model IDは既存adapterと同じ`Qwen/Qwen3-VL-4B-Instruct`とする。
- 調査時点でQwen3-VL checkpointはlocal cacheに見つかっていない。モデルdownloadはrepository外のHugging Face cacheへ行い、weightをGit管理しない。

## 確定したruntime方針

- 使用できる物理GPUは2番と3番である。source code、config file、repository内のscriptには`CUDA_VISIBLE_DEVICES`を設定しない。
- 実行時だけ、shellまたはjob launcherで`CUDA_VISIBLE_DEVICES=2`、`CUDA_VISIBLE_DEVICES=3`、または`CUDA_VISIBLE_DEVICES=2,3`を指定する。指定後にPythonが見るlogical device番号は0または0・1になるため、code内で物理番号2・3を仮定しない。
- Qwen checkpointはHugging Faceの`from_pretrained(model_id)`で取得・loadする。local checkpoint pathを前提にせず、取得済みweightはHugging Face cacheに置く。cache、token、weightはrepositoryへ保存・commitしない。
- 実Qwen runの直前に、選択したvisible GPUの空きmemoryを確認する。GPU選択とmodel loadは実行commandで決め、Python sourceには埋め込まない。

## 採用するAgent構成

同じQwen3-VL instanceを一度だけloadし、各frameで次の二つのgenerationを順に行う。

```text
observation_t = Qwen-VL(question, options, current_image_t)
decision_t = Qwen-VL-text(question, state_{t-1}, observation_t)
state_t = DeterministicReducer(state_{t-1}, decision_t, observation_t)
```

1. **Observation call** は既存のprompt契約を維持する。入力は質問、選択肢、current frame metadata、current RGB画像一枚だけである。
2. **Policy call** は同じQwen3-VLのtext-only generationを使う。入力は質問、選択肢、前時刻のtext state、current observationだけであり、画像は渡さない。
3. **Reducer** はモデルを呼ばない。policy出力のschemaと上限を検証し、同じstate・decision・observationに対して同じnext stateを返す。

過去raw画像、画像embedding、previous/future frame、text state以外の過去入力、final answerは、いずれのcallにも渡さない。

## Text state契約

stateはJSONとして保存・prompt化できる不変構造とする。policy入力に渡すactive stateの上限を初期実装では次に固定する。

```json
{
  "scene_summary": ["安定して成立している事実。最大3項目"],
  "event_ledger": [
    {
      "event_id": "e1",
      "claim": "進行中の出来事または仮説",
      "first_frame": 3,
      "last_evidence_frame": 4,
      "evidence": "最新の根拠"
    }
  ],
  "watch_next": [
    {
      "event_id": "e1",
      "question": "次のcurrent frameで確認する事項"
    }
  ],
  "uncertainties": ["確定できない内容。最大2項目"]
}
```

- `scene_summary`は最大3項目、`event_ledger`は未完了eventを最大5件、`watch_next`は最大2件、`uncertainties`は最大2件とする。
- eventを閉じた履歴はactive stateへ無制限に残さない。frame traceのactionとstate before/afterを恒久的な履歴とする。
- `watch_next.event_id`は存在するopen eventを参照する。eventが閉じたときは対応するwatchを削除する。
- 文字数・token数での追加truncateは行わない。上限を超えるpolicy出力はReducerがrejectしてfail-fastにする。

## Action契約

Policy callはMarkdownを含まない一つのJSON objectを返し、`action`を次から一つ選ぶ。

| Action | Reducerが行う更新 |
| --- | --- |
| `ADD` | 新しいopen event、watch、または場面事実を追加する。 |
| `UPDATE` | ID指定のopen eventのclaim・根拠・最終確認frame、または場面要約を更新する。 |
| `KEEP` | active stateを変更しない。 |
| `FLAG_UNCERTAIN` | 観測だけでは確定できない内容をuncertaintiesへ追加または更新する。 |
| `CLOSE_EVENT` | ID指定のeventをconfirmedまたはrejectedとしてtraceへ残し、active eventと対応watchから除く。 |

全actionは`reason`と`confidence`を持つ。`ADD`、`UPDATE`、`CLOSE_EVENT`は対象eventまたは更新payloadを必須とする。未知ID、上限超過、矛盾するwatch参照、JSON parse失敗はReducer validation errorとして停止する。

## Trace契約

既存の`frames.jsonl`の1 frame 1行という保存契約を維持する。Agent実行時は同じ行に次を追加する。

- observation prompt version、observation text、観測callのmodel ID・generation parameters・処理時間
- `state_before`
- policy prompt version、policy model ID・generation parameters・処理時間
- raw policy response、parse/validation結果、action、reason、confidence
- `state_after`
- Agent callまたはReducerが失敗した場合のerror

Observationまたはpolicy callが失敗した場合も、既存の`JsonlTraceWriter`で当該frameまでの情報をflushしてから例外を再送出する。自動retryは追加しない。

## 実装Stepとbranch

基準branchから、検証済みの直前Step branchを親にして次のbranchを切る。micro Stepはbranchを増やさず、それぞれ個別commitにする。commit titleの後には、対象file・変更内容・理由・検証・次の作業を自然な日本語5〜6行で記す。

```text
feat/step-04-qwen-observation
└── feat/step-05-qwen-runtime
    └── feat/step-06-agent-text-state
        └── feat/step-07-agent-reproducibility
```

### Step 5: Qwen runtimeを準備・検証する

#### 目的

依存関係、CUDA、model cache、checkpoint loadを、Agent実装から分離して確認する。モデルdownload、load、one-frame generationの失敗原因をstate実装と混同しない。

#### Micro Step

1. `docs: document qwen runtime setup`
   - `.venv`の利用、既存package version、default model ID、Hugging Face cacheをrepository外へ置く規則、モデルweightをcommitしない規則を文書化する。
2. `feat: add qwen runtime preflight`
   - Python/torch/Transformers version、CUDA availability、device count、Qwen class import、指定model cacheの存在だけを確認する短いCLIを追加する。preflightはdownloadやmodel loadを行わない。
3. `test: cover qwen runtime preflight`
   - subprocessやmockで、必要runtime情報とmodel未取得状態の表示を検証する。
4. **外部実行（commitしない）**
   - preflight合格後、実行commandで`CUDA_VISIBLE_DEVICES=2`または`3`（必要時は`2,3`）を指定し、Hugging Faceの`from_pretrained("Qwen/Qwen3-VL-4B-Instruct")`でcheckpointをcacheへ取得・loadする。network、認証、disk容量、選択GPUの空きmemoryを実行直前に確認する。モデルweight、cache、tokenをrepositoryへ置かない。
5. `test: run qwen load and one-frame smoke`
   - 実checkpointをloadし、ID 224の1 frameで`--observe`を実行する。JSONLにmodel ID、generation parameters、観測文、処理時間が保存されることを確認する。この実行結果はGit commitへ含めない。
6. **Step末尾smoke（commitしない）**
   - ID 1の5 frameを`--observe`で処理し、current image一枚につき観測callが一回、順序付きJSONLが5行であることを確認する。

#### 完了条件

指定checkpointがrepository外cacheからloadでき、ID 224の1 frameとID 1の5 frameで、既存のcurrent-image-only観測traceが得られる。download、load、生成の失敗時はAgent branchを作らず、runtime問題として原因を記録する。

### Step 6: Text-state Agentを追加する

#### 目的

前stateとcurrent observationだけを使い、Agentがactionを選び、Reducerがbounded text stateを決定的に更新する経路を追加する。

#### Micro Step

1. `feat: add agent state and action contracts`
   - `AgentState`、open event、watch item、uncertainty、`AgentDecision`とaction enumを追加する。state上限とaction必須fieldをconstructor validationで固定する。
2. `feat: add deterministic agent reducer`
   - action別のstate更新、event/watch整合性、上限検証、close時のactive state削除を実装する。ReducerはQwenや画像を受け取らない。
3. `feat: add qwen text policy adapter`
   - 既存Qwen adapterを、一度loadしたmodelからtext-only generationも行える形へ拡張する。policy promptはquestion、options、`state_before`、current observationだけを受け、strict JSON decisionを要求する。
4. `feat: append agent state trace`
   - observation traceへstate before/after、raw policy output、action、validation、policy metadataを追記する。
5. `feat: add agent observation pipeline`
   - 各frameで既存current-image observation call、text-only policy call、Reducer、JSONL writeを因果順に接続する。t=0は空stateから始め、t>=1は直前のtext stateだけを入力にする。
6. `test: cover causal text-state agent`
   - fake observation modelとfake text policyで、t=0空state、t>=1の前state入力、current image一枚、policyへの画像不在、action全種、invalid decision、上限、Reducer replay、future入力不在を検証する。

#### 完了条件

fake modelのtraceから、各frameのobservation、state before、action、state afterを因果順に再生できる。画像入力は観測callのcurrent image一枚だけであり、policy callとReducerへ画像が渡らない。

### Step 7: Agent実行の再現性を整える

#### 目的

短い実Qwen Agent runを、dataset・model・code・state契約から追跡できるようにする。

#### Micro Step

1. `docs: document agent text-state run`
   - Qwen cache準備、preflight、ID 1のAgent run、JSONLの確認方法、未実施の大規模評価を文書化する。
2. `feat: add agent run metadata`
   - manifest hash、record ID、frame count、sampling rule、model ID/revision、package versions、code revision、CLI引数、state schema/prompt versionをrun metadataへ保存する。
3. `test: verify agent trace metadata`
   - 必須metadata、non-overwrite、state/action trace schemaをfake modelで検証する。
4. **Step末尾smoke（commitしない）**
   - 実QwenでID 1の5 frame Agent runを行い、5行のtrace、各行のstate遷移、画像入力境界を確認する。

#### 完了条件

traceとmetadataから、どのrecordをどのmodel・code・state契約で処理したか追跡できる。ID 1の5 frame runで、current-image observationとtext-only policyの二callが各frameで保存される。

## 検証と実行境界

- 通常の実装検証: unit test、compile/import check、CLI help、fake model integration test。
- 実Qwen short smoke: ID 224の1 frame、ID 1の5 frameだけ。モデルdownloadとGPU generationを伴うため、実行時に別途開始指示を確認する。
- 対象外: 957件全体実行、長時間GPU job、学習・LoRA、final QA、accuracy、Agent品質比較、frame skip・再観察・可変chunk。
- `sequential_loader`と`2026_09_hayashi_streaming_video_qa`は変更しない。既存のdecode-only CLIとcurrent-image-only observation経路を維持する。

## Blocking / Non-blocking

### Blocking（実行時）

- checkpointがlocal cacheにないため、Step 5のモデルdownloadにはnetwork、必要ならHugging Face認証、十分なdisk容量が必要である。
- 実Qwen load前に、GPU 2・3のうち実行commandでvisibleにするdeviceの空きmemoryを確認する。GPU選択や他jobへの影響を推測で決めない。
- checkpoint downloadまたは実GPU generationは、このdraft作成では実行しない。実装・実行を開始するときに明示指示を受ける。

### Non-blocking

- Qwenのdtype、device map、max token数は既存CLIの選択肢を保ち、初期smokeでは実行時に指定した値をtrace metadataへ残す。
- policy promptの日本語・英語表現は、strict JSON、入力境界、action schemaを維持する範囲で既存prompt styleに合わせる。
- state内の文字列表現はJSON schemaと上限を守る範囲で決める。

## 成功条件

1. Qwen3-VL checkpointをrepository外cacheからloadし、実QwenでID 224の1 frame observation traceを保存できる。
2. ID 1の5 frame observation runで、各frameにcurrent image一枚だけが渡される。
3. Agent runで、各frameにobservation、state before、action、reason、state afterがJSONLへ保存される。
4. policy callとReducerは画像を受け取らず、t>=1で前frameのtext stateだけを受け取る。
5. fake model testで全action、state上限、invalid JSON/action、future入力の不在、Reducer replayを確認できる。
6. 既存のdecode-only traceと`--observe` observation-only経路のtestが維持される。

## 実装結果（2026-09-16）

- Step 5のQwen runtimeとStep 6のtext-state Agent、Step 7のrun metadataを実装した。最終実装branchは`feat/step-07-agent-reproducibility`で、headは`0288519`である。
- unit / CLI / fake model integration testは31件すべて通過した。
- 実Qwen3-VLでは、ID 224を1 frame、ID 1を5 frame処理した。ID 1のtraceは5行すべて成功し、frame 0で`ADD`、frame 1から4で同じeventの`UPDATE`を記録した。
- 実行artifactはGit管理せず、短時間smokeとして`/tmp/egocross-qwen-agent-smoke/`に置いた。model weightとHugging Face cacheもrepository外に置いた。
- 最終QA、accuracy、957件全体実行、Agent品質の結論は対象外のままである。

## Approval Gate

このspecはdraftである。承認後にbranch作成・コード変更・commitを開始できる。モデルdownloadと実GPU generationは、承認後も実行直前の明示指示を必要とする。

# Implementation Handoff

- approved spec: 承認後は本spec。
- 実装目的: current-image observationを保ったtext-state Agentと短い実Qwen smokeを追加する。
- 基準repository/commit: `feat/step-04-qwen-observation` / `37babe1`。
- 変更scope: Qwen runtime preflight、Qwen text-only policy、state/action/reducer、agent trace、実行文書とtest。
- 対象外・維持条件: 過去raw画像・future frame・final QA・大規模実行を追加せず、既存観察経路を維持する。
- success criteria: 上記「成功条件」に従う。
- 許可されている短時間検証: unit/compile/CLI/fake model test。実Qwenは承認後に別途開始指示。
- 長時間runの許可状態: 未許可。
- 未検証予定: checkpoint download後の実Qwen ID 224・ID 1 smoke。
